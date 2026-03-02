"""Embedded chat page for the main Gradio app."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import shorten
from typing import Any

import gradio as gr
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from src.chain import build_rag_chain
from src.retriever import get_retriever
from src.vectorstore import get_vectorstore

CHAT_LOGS_DIR = Path("data/chat_logs")
_TITLE_WIDTH = 56
_CHAIN_CACHE: Any | None = None
_RETRIEVER_CACHE: Any | None = None


@dataclass(slots=True)
class ChatPageComponents:
    group: gr.Group
    back_button: gr.Button


def _default_conversation_state() -> dict[str, Any]:
    return {
        "conversation_id": None,
        "file_path": None,
        "title": None,
    }


def _conversation_state_for(path: Path | None, title: str | None) -> dict[str, Any]:
    if path is None:
        return _default_conversation_state()

    return {
        "conversation_id": path.stem,
        "file_path": str(path.resolve()),
        "title": title,
    }


def _conversation_path_from_state(conversation_state: dict[str, Any] | None) -> Path | None:
    if not isinstance(conversation_state, dict):
        return None

    file_path = conversation_state.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        return None
    return Path(file_path)


def _vectorstore_status() -> tuple[bool, str]:
    try:
        vectorstore = get_vectorstore()
        count = vectorstore._collection.count()
    except Exception as exc:
        return (
            False,
            "Klarte ikke å åpne vectorstore. Kjør ingest først:\n"
            "`PYTHONPATH=. python -m scripts.ingest`\n"
            f"Detaljer: {exc}",
        )

    if count <= 0:
        return (
            False,
            "Vectorstore er tom. Kjør ingest først:\n"
            "`PYTHONPATH=. python -m scripts.ingest`",
        )

    return True, f"Vectorstore er klar med {count} lagrede tekstbiter."


def _status_markdown() -> str:
    ready, vectorstore_message = _vectorstore_status()
    badge = "Klar" if ready else "Trenger ingest"
    return f"Status: **{badge}**\n\n{vectorstore_message}"


def _compose_status(
    *,
    message: str = "",
    warnings: Sequence[str] | None = None,
) -> str:
    parts = [_status_markdown()]
    if message:
        parts.append(message)
    if warnings:
        warning_lines = "\n".join(f"- {warning}" for warning in warnings)
        parts.append(f"**Advarsler:**\n{warning_lines}")
    return "\n\n".join(part for part in parts if part)


def _empty_sources_markdown() -> str:
    return "_Ingen kilder for dette svaret ennå._"


def _get_chain():
    global _CHAIN_CACHE
    if _CHAIN_CACHE is None:
        _CHAIN_CACHE = build_rag_chain()
    return _CHAIN_CACHE


def _get_retriever():
    global _RETRIEVER_CACHE
    if _RETRIEVER_CACHE is None:
        _RETRIEVER_CACHE = get_retriever()
    return _RETRIEVER_CACHE


def _normalise_message_role(role: object) -> str | None:
    if not isinstance(role, str):
        return None

    lowered = role.strip().lower()
    if lowered in {"user", "human"}:
        return "user"
    if lowered in {"assistant", "ai", "bot"}:
        return "assistant"
    return None


def _coerce_messages(payload: object) -> list[dict[str, str]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("messages"), list):
            payload = payload["messages"]
        elif isinstance(payload.get("history"), list):
            payload = payload["history"]

    if not isinstance(payload, list):
        return []

    messages: list[dict[str, str]] = []
    for item in payload:
        if isinstance(item, dict):
            role = _normalise_message_role(item.get("role"))
            content = item.get("content")
            if role and isinstance(content, str) and content.strip():
                messages.append({"role": role, "content": content})
            continue

        if isinstance(item, (list, tuple)):
            user_text = item[0] if len(item) > 0 else None
            assistant_text = item[1] if len(item) > 1 else None
            if isinstance(user_text, str) and user_text.strip():
                messages.append({"role": "user", "content": user_text})
            if isinstance(assistant_text, str) and assistant_text.strip():
                messages.append({"role": "assistant", "content": assistant_text})

    return messages


def _read_conversation_file(path: Path) -> tuple[list[dict[str, str]], str | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stored_title = None
    if isinstance(payload, dict):
        title = payload.get("title")
        if isinstance(title, str) and title.strip():
            stored_title = title.strip()
    return _coerce_messages(payload), stored_title


def _conversation_title(messages: Sequence[dict[str, str]], fallback: str) -> str:
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if role == "user" and isinstance(content, str) and content.strip():
            flattened = " ".join(content.split())
            return shorten(flattened, width=_TITLE_WIDTH, placeholder="…")
    return fallback


def _format_sidebar_label(conversation: dict[str, Any]) -> str:
    updated_at = conversation.get("updated_at")
    if isinstance(updated_at, datetime):
        updated_label = updated_at.strftime("%d.%m %H:%M")
    else:
        updated_label = "ukjent tid"
    return f"{conversation['title']} - {updated_label}"


def _selector_choices(conversations: Sequence[dict[str, Any]]) -> list[tuple[str, str]]:
    return [
        (_format_sidebar_label(conversation), conversation["conversation_id"])
        for conversation in conversations
    ]


def _conversation_count_text(conversations: Sequence[dict[str, Any]]) -> str:
    count = len(conversations)
    if count == 0:
        return "Ingen tidligere samtaler funnet."
    if count == 1:
        return "1 samtale funnet."
    return f"{count} samtaler funnet."


def _open_conversation_text(title: str | None) -> str:
    return f"Åpen samtale: {title or 'Ingen'}"


def _save_conversation(path: Path, messages: list[dict[str, str]]) -> None:
    CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "conversation_id": path.stem,
        "title": _conversation_title(messages, "Ny samtale"),
        "messages": messages,
    }
    temp_path = path.with_name(f".{path.name}.tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp_path.replace(path)


def _new_conversation_file() -> Path:
    CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    stem = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    candidate = CHAT_LOGS_DIR / f"{stem}.json"
    suffix = 1
    while candidate.exists():
        candidate = CHAT_LOGS_DIR / f"{stem}-{suffix}.json"
        suffix += 1
    return candidate


def _list_conversations_with_warnings() -> tuple[list[dict[str, Any]], list[str]]:
    if not CHAT_LOGS_DIR.exists():
        return [], []

    conversations: list[dict[str, Any]] = []
    warnings: list[str] = []

    for path in sorted(CHAT_LOGS_DIR.glob("*.json")):
        try:
            messages, stored_title = _read_conversation_file(path)
        except Exception as exc:
            warnings.append(f"Hoppet over {path.name}: {exc}")
            continue

        fallback_title = path.stem
        title = stored_title or _conversation_title(messages, fallback_title)
        conversations.append(
            {
                "conversation_id": path.stem,
                "title": title,
                "file_path": str(path.resolve()),
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime),
            }
        )

    conversations.sort(
        key=lambda conversation: conversation["updated_at"],
        reverse=True,
    )
    return conversations, warnings


def _list_conversations() -> list[dict[str, Any]]:
    conversations, _ = _list_conversations_with_warnings()
    return conversations


def _load_conversation(path: Path) -> list[dict[str, str]]:
    messages, _ = _read_conversation_file(path)
    return messages


def _sidebar_updates(
    selected_id: str | None,
    *,
    selected_title: str | None = None,
    status_message: str = "",
    warnings: Sequence[str] | None = None,
) -> tuple[Any, str, str, str]:
    conversations = _list_conversations()
    selected_meta = next(
        (
            conversation
            for conversation in conversations
            if conversation["conversation_id"] == selected_id
        ),
        None,
    )
    resolved_title = selected_meta["title"] if selected_meta is not None else selected_title
    resolved_value = selected_meta["conversation_id"] if selected_meta is not None else None
    return (
        gr.update(choices=_selector_choices(conversations), value=resolved_value),
        _conversation_count_text(conversations),
        _compose_status(message=status_message, warnings=warnings),
        _open_conversation_text(resolved_title),
    )


def _to_langchain_history(
    history: Sequence[dict[str, Any]] | None,
) -> list[HumanMessage | AIMessage]:
    messages: list[HumanMessage | AIMessage] = []
    if not history:
        return messages

    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if not isinstance(content, str) or not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _display_title(doc: Document) -> str:
    raw_title = doc.metadata.get("source_file")
    if not raw_title or not isinstance(raw_title, str):
        source_path = doc.metadata.get("source_path")
        if isinstance(source_path, str) and source_path.strip():
            raw_title = Path(source_path).name
        else:
            return "Pensum"

    title = raw_title.strip().replace("_", " ")
    if title.lower().endswith(".pdf"):
        title = title[:-4]
    return title or "Pensum"


def _render_sources_markdown(docs: list[Document]) -> str:
    if not docs:
        return _empty_sources_markdown()

    lines: list[str] = []
    for rank, doc in enumerate(docs, 1):
        raw_page = doc.metadata.get("page")
        if raw_page == 0:
            page = "0"
        else:
            page_str = "" if raw_page is None else str(raw_page).strip()
            page = page_str if page_str else "?"

        title = _display_title(doc)
        excerpt = shorten(" ".join(doc.page_content.split()), width=900, placeholder="…")

        lines.append(f"### Kilde {rank} - {title} (s. {page})")
        lines.append("")
        lines.append("> " + excerpt.replace("\n", "\n> "))
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _refresh_conversation_list(
    conversation_state: dict[str, Any] | None,
) -> tuple[Any, str, str, str, dict[str, Any]]:
    conversations, warnings = _list_conversations_with_warnings()
    selected_id = None
    selected_title = None
    next_state = _default_conversation_state()

    if isinstance(conversation_state, dict):
        selected_id_value = conversation_state.get("conversation_id")
        if isinstance(selected_id_value, str):
            selected_id = selected_id_value
        selected_title_value = conversation_state.get("title")
        if isinstance(selected_title_value, str):
            selected_title = selected_title_value

    selected_meta = next(
        (
            conversation
            for conversation in conversations
            if conversation["conversation_id"] == selected_id
        ),
        None,
    )
    if selected_meta is not None:
        next_state = _conversation_state_for(
            Path(selected_meta["file_path"]),
            selected_meta["title"],
        )

    selector_update, count_text, status_text, open_text = _sidebar_updates(
        selected_id if selected_meta is not None else None,
        selected_title=selected_meta["title"] if selected_meta is not None else None,
        status_message="Samtalelisten er oppdatert.",
        warnings=warnings,
    )
    return selector_update, count_text, status_text, open_text, next_state


def _load_selected_conversation(
    conversation_id: str | None,
) -> tuple[str, list[dict[str, str]], str, str, dict[str, Any], Any, str, str]:
    conversations, warnings = _list_conversations_with_warnings()
    selected_meta = next(
        (
            conversation
            for conversation in conversations
            if conversation["conversation_id"] == conversation_id
        ),
        None,
    )

    if selected_meta is None:
        selector_update, count_text, status_text, open_text = _sidebar_updates(
            None,
            status_message="Samtalen ble ikke funnet.",
            warnings=warnings,
        )
        return (
            "",
            [],
            status_text,
            _empty_sources_markdown(),
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
        )

    path = Path(selected_meta["file_path"])
    try:
        messages = _load_conversation(path)
    except Exception as exc:
        selector_update, count_text, status_text, open_text = _sidebar_updates(
            None,
            status_message=f"Klarte ikke å laste samtalen: {exc}",
            warnings=warnings,
        )
        return (
            "",
            [],
            status_text,
            _empty_sources_markdown(),
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
        )

    title = _conversation_title(messages, selected_meta["title"])
    next_state = _conversation_state_for(path, title)
    selector_update, count_text, status_text, open_text = _sidebar_updates(
        conversation_id,
        selected_title=title,
        status_message=f"Lastet samtale: {title}.",
        warnings=warnings,
    )
    return (
        "",
        messages,
        status_text,
        _empty_sources_markdown(),
        next_state,
        selector_update,
        count_text,
        open_text,
    )


def _create_new_conversation() -> tuple[str, list[dict[str, str]], str, str, dict[str, Any], Any, str, str]:
    path = _new_conversation_file()
    _save_conversation(path, [])
    next_state = _conversation_state_for(path, "Ny samtale")
    conversations, warnings = _list_conversations_with_warnings()
    selected_meta = next(
        (
            conversation
            for conversation in conversations
            if conversation["conversation_id"] == path.stem
        ),
        None,
    )
    title = selected_meta["title"] if selected_meta is not None else "Ny samtale"
    next_state["title"] = title

    selector_update, count_text, status_text, open_text = _sidebar_updates(
        path.stem,
        selected_title=title,
        status_message="Ny samtale opprettet.",
        warnings=warnings,
    )
    return (
        "",
        [],
        status_text,
        _empty_sources_markdown(),
        next_state,
        selector_update,
        count_text,
        open_text,
    )


def _chat(
    user_message: str,
    history: list[dict[str, Any]] | None,
    conversation_state: dict[str, Any] | None,
) -> tuple[str, list[dict[str, str]], str, str, dict[str, Any], Any, str, str]:
    visible_history = [
        message
        for message in (history or [])
        if isinstance(message, dict)
        and message.get("role") in {"user", "assistant"}
        and isinstance(message.get("content"), str)
    ]
    text = (user_message or "").strip()

    current_path = _conversation_path_from_state(conversation_state)
    current_title = None
    current_id = None
    if isinstance(conversation_state, dict):
        title_value = conversation_state.get("title")
        if isinstance(title_value, str):
            current_title = title_value
        id_value = conversation_state.get("conversation_id")
        if isinstance(id_value, str):
            current_id = id_value

    if not text:
        _, warnings = _list_conversations_with_warnings()
        selector_update, count_text, status_text, open_text = _sidebar_updates(
            current_id,
            selected_title=current_title,
            warnings=warnings,
        )
        return (
            "",
            visible_history,
            status_text,
            _empty_sources_markdown(),
            conversation_state if isinstance(conversation_state, dict) else _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
        )

    if current_path is None:
        current_path = _new_conversation_file()
        _save_conversation(current_path, [])
        current_id = current_path.stem
        current_title = "Ny samtale"

    persisted_messages: list[dict[str, str]]
    try:
        persisted_messages = _load_conversation(current_path)
    except Exception:
        persisted_messages = []

    ready, vectorstore_message = _vectorstore_status()
    if not ready:
        assistant_message = (
            "Kan ikke svare ennå fordi vectorstore ikke er klar.\n\n"
            f"{vectorstore_message}"
        )
        docs: list[Document] = []
    else:
        docs = []
        try:
            retrieved_docs = _get_retriever().invoke(text)
            if isinstance(retrieved_docs, list):
                docs = [doc for doc in retrieved_docs if isinstance(doc, Document)]
            assistant_message = str(
                _get_chain().invoke(
                    {
                        "question": text,
                        "chat_history": _to_langchain_history(persisted_messages),
                    }
                )
            )
        except Exception as exc:
            assistant_message = (
                "Det oppstod en feil under generering av svar.\n\n"
                f"Detaljer: {exc}"
            )
            docs = []

    new_turn = [
        {"role": "user", "content": text},
        {"role": "assistant", "content": assistant_message},
    ]
    updated_history = visible_history + new_turn
    persisted_messages.extend(new_turn)
    _save_conversation(current_path, persisted_messages)

    title = _conversation_title(persisted_messages, current_title or current_path.stem)
    next_state = _conversation_state_for(current_path, title)
    _, warnings = _list_conversations_with_warnings()
    selector_update, count_text, status_text, open_text = _sidebar_updates(
        current_path.stem,
        selected_title=title,
        warnings=warnings,
    )

    return (
        "",
        updated_history,
        status_text,
        _render_sources_markdown(docs),
        next_state,
        selector_update,
        count_text,
        open_text,
    )


def _clear_chat_view(
    conversation_state: dict[str, Any] | None,
) -> tuple[str, list[dict[str, str]], str, str, dict[str, Any], Any, str, str]:
    # Deliberately clears only the visible chat UI. The stored conversation file stays unchanged.
    current_id = None
    current_title = None
    current_state = conversation_state if isinstance(conversation_state, dict) else _default_conversation_state()

    if isinstance(current_state.get("conversation_id"), str):
        current_id = current_state["conversation_id"]
    if isinstance(current_state.get("title"), str):
        current_title = current_state["title"]

    _, warnings = _list_conversations_with_warnings()
    selector_update, count_text, status_text, open_text = _sidebar_updates(
        current_id,
        selected_title=current_title,
        status_message="Chatvisningen er tømt. Lagret samtale er uendret.",
        warnings=warnings,
    )
    return (
        "",
        [],
        status_text,
        _empty_sources_markdown(),
        current_state,
        selector_update,
        count_text,
        open_text,
    )


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    initial_conversations, initial_warnings = _list_conversations_with_warnings()
    initial_selector_choices = _selector_choices(initial_conversations)
    initial_count_text = _conversation_count_text(initial_conversations)

    with gr.Group(visible=visible) as group:
        conversation_state = gr.State(_default_conversation_state())

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Samtaler")
                with gr.Row():
                    new_conversation_button = gr.Button("Ny samtale", variant="secondary")
                    refresh_button = gr.Button("Oppdater")
                conversation_selector = gr.Radio(
                    choices=initial_selector_choices,
                    value=None,
                    label=None,
                )
                conversation_count = gr.Markdown(initial_count_text)

            with gr.Column(scale=4):
                gr.Markdown("# Chat")
                gr.Markdown("Chat med tutor (RAG).")
                open_conversation = gr.Markdown(_open_conversation_text(None))
                status = gr.Markdown(_compose_status(warnings=initial_warnings))
                chatbot = gr.Chatbot(type="messages", height=700, label="Chat")
                message = gr.Textbox(
                    label="Melding",
                    placeholder="Spør om minnehåndtering, paging, scheduling, ...",
                    lines=2,
                )
                with gr.Accordion("Kilder", open=False):
                    sources = gr.Markdown(_empty_sources_markdown())

                with gr.Row():
                    send_button = gr.Button("Send", variant="primary")
                    clear_button = gr.Button("Tøm chat")
                    back_button = gr.Button("Tilbake")

    chat_outputs = [
        message,
        chatbot,
        status,
        sources,
        conversation_state,
        conversation_selector,
        conversation_count,
        open_conversation,
    ]

    send_button.click(
        fn=_chat,
        inputs=[message, chatbot, conversation_state],
        outputs=chat_outputs,
    )
    clear_button.click(
        fn=_clear_chat_view,
        inputs=[conversation_state],
        outputs=chat_outputs,
    )
    conversation_selector.change(
        fn=_load_selected_conversation,
        inputs=[conversation_selector],
        outputs=chat_outputs,
    )
    new_conversation_button.click(
        fn=_create_new_conversation,
        inputs=None,
        outputs=chat_outputs,
    )
    refresh_button.click(
        fn=_refresh_conversation_list,
        inputs=[conversation_state],
        outputs=[
            conversation_selector,
            conversation_count,
            status,
            open_conversation,
            conversation_state,
        ],
    )

    return ChatPageComponents(group=group, back_button=back_button)
