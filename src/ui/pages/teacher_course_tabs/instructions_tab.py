"""Teacher course instructions tab UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.router import ROUTE_TEACHER_COURSE
from src.ui.state import COURSE_ID_KEY, auth_token

MAX_COURSE_INSTRUCTIONS_CHARS = 3000


@dataclass(slots=True)
class TeacherCourseInstructionsTabComponents:
    group: gr.Group
    course_instructions_input: gr.Textbox
    course_instructions_counter: gr.Markdown
    save_course_instructions_button: gr.Button
    status_text: gr.Markdown


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def _course_instructions_counter_text(instructions_text: str | None) -> str:
    instruction_length = len(str(instructions_text or ""))
    return f"Tegn brukt: {instruction_length}/{MAX_COURSE_INSTRUCTIONS_CHARS}"


def build_teacher_course_instructions_tab() -> TeacherCourseInstructionsTabComponents:
    with gr.Group() as group:
        with gr.Group():
            gr.Markdown(
                "Legg til kursinstruksjoner som blir lagt til systemprompten for dette faget."
            )
            course_instructions_input = gr.Textbox(
                label="Instruksjoner (maks 3000 tegn)",
                placeholder=(
                    "Eksempel: Prioriter pensumbegreper fra uke 1–5, bruk norske fagtermer, "
                    "og gi korte stegvise hint før fasitsvar."
                ),
                lines=8,
                max_lines=12,
            )
            course_instructions_counter = gr.Markdown(_course_instructions_counter_text(""))
            save_course_instructions_button = gr.Button(
                "Lagre instruksjoner",
                variant="primary",
            )
        status_text = gr.Markdown()

    return TeacherCourseInstructionsTabComponents(
        group=group,
        course_instructions_input=course_instructions_input,
        course_instructions_counter=course_instructions_counter,
        save_course_instructions_button=save_course_instructions_button,
        status_text=status_text,
    )


def _empty_course_instructions_updates(status_text: str = "") -> tuple[Any, str, str]:
    return gr.update(value=""), _course_instructions_counter_text(""), status_text


def _instruction_value(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    return str(payload.get("course_specific_instructions") or "")


def teacher_course_instructions_updates(state: dict[str, Any]) -> tuple[Any, str, str]:
    if state.get("route") != ROUTE_TEACHER_COURSE:
        return _empty_course_instructions_updates()

    course_id = _current_course_id(state)
    if not course_id:
        return _empty_course_instructions_updates("Fant ikke faget.")

    token = auth_token(state)
    if not token:
        return _empty_course_instructions_updates("Sessionen er utløpt — logg inn på nytt.")

    success, message, payload = _course_api.get_course_instructions(token, course_id)
    if not success:
        return _empty_course_instructions_updates(message)

    instructions_text = _instruction_value(payload)
    return (
        gr.update(value=instructions_text),
        _course_instructions_counter_text(instructions_text),
        "",
    )


def teacher_course_instructions_input_update(_state: dict[str, Any]) -> Any:
    input_update, _counter_text, _status_text = teacher_course_instructions_updates(_state)
    return input_update


def teacher_course_instructions_counter_update(_state: dict[str, Any]) -> str:
    _input_update, counter_text, _status_text = teacher_course_instructions_updates(_state)
    return counter_text


def teacher_course_instructions_status_update(_state: dict[str, Any]) -> str:
    _input_update, _counter_text, status_text = teacher_course_instructions_updates(_state)
    return status_text


def handle_course_instructions_input(instructions_text: str | None) -> str:
    return _course_instructions_counter_text(instructions_text)


def handle_save_course_instructions(
    state: dict[str, Any],
    instructions_text: str | None,
) -> tuple[Any, str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        counter_text = _course_instructions_counter_text(instructions_text)
        return gr.update(value=instructions_text or ""), counter_text, "Fant ikke faget."

    token = auth_token(state)
    if not token:
        counter_text = _course_instructions_counter_text(instructions_text)
        return (
            gr.update(value=instructions_text or ""),
            counter_text,
            "Sessionen er utløpt — logg inn på nytt.",
        )

    raw_instructions = str(instructions_text or "")
    if len(raw_instructions) > MAX_COURSE_INSTRUCTIONS_CHARS:
        counter_text = _course_instructions_counter_text(raw_instructions)
        return (
            gr.update(value=raw_instructions),
            counter_text,
            f"Instruksjonene er for lange. Maks {MAX_COURSE_INSTRUCTIONS_CHARS} tegn.",
        )

    cleaned_instructions = raw_instructions.strip()
    payload_instructions = cleaned_instructions or None

    success, message, _course = _course_api.update_course_instructions(
        token,
        course_id,
        payload_instructions,
    )
    next_input_value = cleaned_instructions if success else raw_instructions
    return (
        gr.update(value=next_input_value),
        _course_instructions_counter_text(next_input_value),
        message,
    )
