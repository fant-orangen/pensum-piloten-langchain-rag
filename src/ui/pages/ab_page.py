"""A/B comparison page for evaluating RAG vs. non-RAG answer quality.

Presents randomly ordered questions to the user, fetches answers from both
systems in parallel, and collects slider-based preference ratings that are
persisted as JSONL records and optionally exported as JSON or CSV.
"""

from __future__ import annotations

import csv
import json
import os
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

import gradio as gr

from src.config import get_settings

QUESTIONS_PATH = Path("data/questions.json")
AB_RUNS_DIR = Path("data/ab_runs")

DEFAULT_QUESTIONS = [
    "What is the difference between a process and a thread?",
    "How does preemptive scheduling differ from cooperative scheduling?",
    "What is a race condition, and how can mutexes help avoid it?",
    "Explain deadlock and the four Coffman conditions.",
    "What problem does virtual memory solve, and how does paging work?",
    "Why do operating systems use system calls instead of direct hardware access?",
    "How does a file system map a file name to data blocks on disk?",
    "What is the purpose of a TLB in memory management?",
    "Compare user-mode and kernel-mode execution.",
    "When should an OS use round-robin scheduling versus shortest-job-first?",
]

_NO_ANSWER_TEXT = "_Svar er ikke generert ennå._"

AB_PAGE_CSS = """
.answer-box {
    min-height: 340px;
    max-height: 340px;
    overflow-y: auto;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    padding: 12px;
    background: #ffffff;
}
"""


@dataclass(slots=True)
class ABPageComponents:
    """Holds the top-level Gradio group and optional back button for the A/B page."""

    group: gr.Group
    back_button: gr.Button | None


def _backend_base_url() -> str:
    """Return the base URL for the backend API, preferring the AB_BACKEND_URL environment variable."""
    env_url = os.getenv("AB_BACKEND_URL")
    if env_url:
        return env_url.rstrip("/")

    settings = get_settings()
    host = settings.api_host
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    return f"http://{host}:{settings.api_port}"


def _load_questions() -> list[str]:
    """Load questions from the JSON file at QUESTIONS_PATH, falling back to DEFAULT_QUESTIONS on any error."""
    if QUESTIONS_PATH.exists():
        try:
            payload = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
            if isinstance(payload, list) and all(isinstance(q, str) and q.strip() for q in payload):
                return [q.strip() for q in payload]
            if isinstance(payload, dict):
                questions = payload.get("questions")
                if isinstance(questions, list) and all(
                    isinstance(q, str) and q.strip() for q in questions
                ):
                    return [q.strip() for q in questions]
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_QUESTIONS


def _http_json(
    url: str,
    method: str,
    payload: dict[str, Any] | None,
    timeout: float,
) -> dict[str, Any]:
    """Perform an HTTP request and return the decoded JSON response as a dict."""
    headers = {"Accept": "application/json"}
    body: bytes | None = None

    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    req = request.Request(url=url, data=body, method=method, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")

    if not raw:
        return {}

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Backend response is not a JSON object.")
    return parsed


def _check_backend_health(base_url: str) -> tuple[bool, str]:
    """Ping the backend health endpoint and return a (success, status_message) tuple."""
    try:
        response = _http_json(url=f"{base_url}/health", method="GET", payload=None, timeout=5.0)
        status = response.get("status")
        if status == "ok":
            return True, f"Backend-status: tilgjengelig (`{base_url}`)"
        return False, f"Backend-status: uventet svar fra `{base_url}`"
    except Exception as exc:
        return False, f"Backend-status: utilgjengelig (`{base_url}`): {exc}"


def _ask_backend(question: str, mode: str, base_url: str) -> tuple[str, float, str | None]:
    """Send a question to the backend in the given mode and return the answer, latency, and any error string."""
    start = time.perf_counter()
    try:
        response = _http_json(
            url=f"{base_url}/ask",
            method="POST",
            payload={"question": question, "chat_history": [], "mode": mode},
            timeout=120.0,
        )
    except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        latency = time.perf_counter() - start
        return (
            f"**Feil:** klarte ikke å hente svar ({exc}).",
            latency,
            str(exc),
        )

    answer = str(response.get("answer", "")).strip() or "_Ingen svar ble returnert._"
    latency = time.perf_counter() - start
    return answer, latency, None


def _new_session(questions: list[str]) -> dict[str, Any]:
    """Create and return a fresh session state dict with randomly assigned system modes."""
    if random.random() < 0.5:
        system1_mode, system2_mode = "rag", "no_rag"
    else:
        system1_mode, system2_mode = "no_rag", "rag"

    session_id = uuid.uuid4().hex
    return {
        "session_id": session_id,
        "questions": questions,
        "current_index": 0,
        "system1_mode": system1_mode,
        "system2_mode": system2_mode,
        "backend_url": _backend_base_url(),
        "backend_status_text": "Backend-status: sjekker...",
        "answers_by_index": {},
        "results": [],
        "ratings_by_index": {},
        "submitted_indices": [],
        "runs_file": str(AB_RUNS_DIR / f"{session_id}.jsonl"),
    }


def _can_submit(state: dict[str, Any]) -> bool:
    """Return True if the current question has answers and has not yet been submitted."""
    idx = state["current_index"]
    if idx in state["submitted_indices"]:
        return False
    answer = state["answers_by_index"].get(idx)
    if answer is None:
        return False
    return not bool(answer.get("error"))


def _ensure_answers(state: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Fetch answers for the current question from both systems in parallel if not already cached."""
    idx = state["current_index"]
    cached_answer = state["answers_by_index"].get(idx)
    if cached_answer is not None and not bool(cached_answer.get("error")):
        return state, ""

    question = state["questions"][idx]
    base_url = state["backend_url"]
    mode1 = state["system1_mode"]
    mode2 = state["system2_mode"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(_ask_backend, question, mode1, base_url)
        future2 = executor.submit(_ask_backend, question, mode2, base_url)
        system1_answer, latency1, err1 = future1.result()
        system2_answer, latency2, err2 = future2.result()

    has_error = err1 is not None or err2 is not None
    state["answers_by_index"][idx] = {
        "system1_answer": system1_answer,
        "system2_answer": system2_answer,
        "latency_system1": latency1,
        "latency_system2": latency2,
        "error": has_error,
    }

    if has_error:
        state["backend_status_text"] = (
            f"Backend-status: feil ved generering av svar (`{base_url}`)"
        )
        parts = []
        if err1:
            parts.append(f"System 1 feilet: {err1}")
        if err2:
            parts.append(f"System 2 feilet: {err2}")
        return state, " | ".join(parts)
    state["backend_status_text"] = f"Backend-status: tilgjengelig (`{base_url}`)"
    return state, ""


def _render_state(state: dict[str, Any], status_message: str = "") -> tuple[Any, ...]:
    """Produce Gradio update values for all output components from the current session state."""
    idx = state["current_index"]
    total = len(state["questions"])
    question = state["questions"][idx]
    answer_payload = state["answers_by_index"].get(idx)

    if answer_payload is None:
        answer1 = _NO_ANSWER_TEXT
        answer2 = _NO_ANSWER_TEXT
    else:
        answer1 = answer_payload["system1_answer"]
        answer2 = answer_payload["system2_answer"]

    slider_value = state["ratings_by_index"].get(idx, 0)
    slider_interactive = (
        answer_payload is not None
        and idx not in state["submitted_indices"]
        and not bool(answer_payload.get("error"))
    )
    submit_interactive = _can_submit(state)

    return (
        state["backend_status_text"],
        f"### Spørsmål {idx + 1} / {total}",
        f"**{question}**",
        answer1,
        answer2,
        gr.update(value=slider_value, interactive=slider_interactive),
        gr.update(interactive=submit_interactive),
        status_message,
        gr.update(interactive=idx > 0),
        gr.update(interactive=idx < total - 1),
    )


def _initialise_session() -> tuple[Any, ...]:
    """Create a new session, health-check the backend, pre-fetch answers for the first question, and render the initial UI."""
    state = _new_session(_load_questions())
    healthy, health_message = _check_backend_health(state["backend_url"])
    state["backend_status_text"] = health_message

    message = ""
    if healthy:
        state, error_message = _ensure_answers(state)
        if error_message:
            message = f"**Feil:** {error_message}"
    else:
        message = "**Feil:** Backend er utilgjengelig. Start API-serveren og tilbakestill økten."

    return (state, *_render_state(state, message))


def _move_question(state: dict[str, Any], step: int) -> tuple[Any, ...]:
    """Advance or retreat by step questions, ensuring answers are available, and render the new state."""
    total = len(state["questions"])
    current_index = state["current_index"]
    new_index = max(0, min(total - 1, current_index + step))
    state["current_index"] = new_index

    state, error_message = _ensure_answers(state)
    if error_message:
        message = f"**Feil:** {error_message}"
    elif new_index == current_index:
        message = "Ingen flere spørsmål i denne retningen."
    else:
        message = ""
    return (state, *_render_state(state, message))


def _reset_session(_: dict[str, Any]) -> tuple[Any, ...]:
    """Discard the current session and start a fresh one."""
    return _initialise_session()


def _next_question(state: dict[str, Any]) -> tuple[Any, ...]:
    """Move forward by one question."""
    return _move_question(state, step=1)


def _previous_question(state: dict[str, Any]) -> tuple[Any, ...]:
    """Move backward by one question."""
    return _move_question(state, step=-1)


def _append_result(record: dict[str, Any], runs_file: str) -> None:
    """Append a single rating record as a JSON line to the session's JSONL file."""
    AB_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = Path(runs_file)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")


def _submit_rating(
    state: dict[str, Any],
    slider_value: float,
    auto_advance: bool,
) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, Any, Any, Any, Any]:
    """Record the slider rating for the current question, persist it, and optionally advance to the next question."""
    idx = state["current_index"]
    if idx in state["submitted_indices"]:
        return (state, *_render_state(state, "Dette spørsmålet er allerede sendt inn."))

    answer_payload = state["answers_by_index"].get(idx)
    if answer_payload is None:
        return (state, *_render_state(state, "Generer svar før du sender inn en vurdering."))
    if answer_payload.get("error"):
        return (state, *_render_state(state, "Kan ikke sende inn fordi generering av svar feilet."))

    slider_int = int(slider_value)
    state["ratings_by_index"][idx] = slider_int

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": state["session_id"],
        "question_index": idx,
        "question_text": state["questions"][idx],
        "system1_mode": state["system1_mode"],
        "system2_mode": state["system2_mode"],
        "system1_answer": answer_payload["system1_answer"],
        "system2_answer": answer_payload["system2_answer"],
        "slider_value": slider_int,
        "latency_system1": answer_payload["latency_system1"],
        "latency_system2": answer_payload["latency_system2"],
    }

    _append_result(record, state["runs_file"])
    state["results"].append(record)
    state["submitted_indices"].append(idx)

    status_message = "Vurdering lagret."
    if auto_advance and idx < len(state["questions"]) - 1:
        state["current_index"] = idx + 1
        state, error_message = _ensure_answers(state)
        if error_message:
            status_message = f"Vurdering lagret. **Feil:** {error_message}"
        else:
            status_message = "Vurdering lagret. Flyttet til neste spørsmål."

    return (state, *_render_state(state, status_message))


def _export_results(state: dict[str, Any], export_format: str) -> tuple[str, str | None]:
    """Export all submitted ratings to a JSON or CSV file and return a status message and file path."""
    records = state["results"]
    if not records:
        return "Ingen innsendte vurderinger å eksportere ennå.", None

    export_dir = AB_RUNS_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    if export_format == "csv":
        path = export_dir / f"{state['session_id']}-{timestamp}.csv"
        fieldnames = [
            "timestamp",
            "session_id",
            "question_index",
            "question_text",
            "system1_mode",
            "system2_mode",
            "system1_answer",
            "system2_answer",
            "slider_value",
            "latency_system1",
            "latency_system2",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    else:
        path = export_dir / f"{state['session_id']}-{timestamp}.json"
        path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    return f"Eksporterte {len(records)} vurdering(er).", str(path)


def build_ab_page(
    demo: gr.Blocks,
    *,
    visible: bool,
    include_back_button: bool,
) -> ABPageComponents:
    """Build the A/B evaluation Gradio group, wire up all event handlers, and return the page components."""
    session_state = gr.State({})

    with gr.Group(visible=visible) as group:
        if include_back_button:
            back_button = gr.Button("Tilbake")
        else:
            back_button = None

        gr.Markdown("## A/B-evaluering")
        gr.Markdown(
            "Sammenlign **System 1** og **System 2** for hvert spørsmål. "
            "Bruk skyveknappen for å angi preferanse."
        )

        backend_status = gr.Markdown("Backend-status: sjekker...")
        question_counter = gr.Markdown()
        question_text = gr.Markdown()

        with gr.Row():
            with gr.Column():
                gr.Markdown("### System 1")
                system1_answer = gr.Markdown(_NO_ANSWER_TEXT, elem_classes=["answer-box"])
            with gr.Column():
                gr.Markdown("### System 2")
                system2_answer = gr.Markdown(_NO_ANSWER_TEXT, elem_classes=["answer-box"])

        preference_slider = gr.Slider(
            minimum=-2,
            maximum=2,
            step=1,
            value=0,
            label="Preferanse",
            info="-2/-1 foretrekker System 1, 0 er uavgjort, +1/+2 foretrekker System 2",
        )
        auto_advance = gr.Checkbox(
            value=True,
            label="Gå automatisk til neste spørsmål etter innsending",
        )

        with gr.Row():
            submit_button = gr.Button("Send inn vurdering", variant="primary", interactive=False)
            prev_button = gr.Button("Forrige spørsmål", interactive=False)
            next_button = gr.Button("Neste spørsmål", interactive=False)
            reset_button = gr.Button("Tilbakestill økt")

        status_text = gr.Markdown()

        with gr.Row():
            export_format = gr.Radio(
                choices=["json", "csv"],
                value="json",
                label="Eksportformat",
            )
            export_button = gr.Button("Eksporter resultater")
        export_file = gr.File(label="Last ned eksport", interactive=False)

    init_outputs = [
        session_state,
        backend_status,
        question_counter,
        question_text,
        system1_answer,
        system2_answer,
        preference_slider,
        submit_button,
        status_text,
        prev_button,
        next_button,
    ]

    demo.load(fn=_initialise_session, inputs=None, outputs=init_outputs)
    next_button.click(
        fn=_next_question,
        inputs=[session_state],
        outputs=init_outputs,
    )
    prev_button.click(
        fn=_previous_question,
        inputs=[session_state],
        outputs=init_outputs,
    )
    submit_button.click(
        fn=_submit_rating,
        inputs=[session_state, preference_slider, auto_advance],
        outputs=init_outputs,
    )
    reset_button.click(
        fn=_reset_session,
        inputs=[session_state],
        outputs=init_outputs,
    )
    export_button.click(
        fn=_export_results,
        inputs=[session_state, export_format],
        outputs=[status_text, export_file],
    )

    return ABPageComponents(group=group, back_button=back_button)


def build_ab_app() -> gr.Blocks:
    """Build and return a standalone Gradio Blocks application containing only the A/B evaluation page."""
    with gr.Blocks(css=AB_PAGE_CSS, title="A/B-evaluering") as demo:
        build_ab_page(demo, visible=True, include_back_button=False)

    return demo
