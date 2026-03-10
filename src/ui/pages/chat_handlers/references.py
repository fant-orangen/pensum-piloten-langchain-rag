"""Reference panel and selection helpers for chat handlers."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.ui.pages.chat_handlers.contracts import (
    _REFERENCE_DEFAULT_STATUS,
    _REFERENCE_NO_SOURCES_STATUS,
    _REFERENCE_USER_SELECTED_STATUS,
    ChatReferenceRows,
    ChatSourceHistory,
    ChatVisibleHistory,
)
from src.ui.pages.chat_state import (
    ChatSourceEntry,
    ChatConversationState,
    coerce_source_history,
    empty_reference_rows,
    latest_assistant_sources,
    normalize_conversation_state,
    normalize_source_entry,
    reference_rows_for_sources,
    visible_history_from_source_history,
)
from src.ui.services.conversation_service import get_message_sources


def _empty_reference_rows() -> ChatReferenceRows:
    return empty_reference_rows()


def _normalize_reference_entry(value: Any) -> ChatSourceEntry | None:
    return normalize_source_entry(value)


def _reference_rows_for_sources(sources: list[dict[str, Any]] | None) -> ChatReferenceRows:
    return reference_rows_for_sources(sources)


def _visible_history_from_source_history(
    source_history: list[dict[str, Any]] | None,
) -> ChatVisibleHistory:
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in visible_history_from_source_history(source_history)
    ]


def _coerce_source_history(
    visible_history: list[dict[str, Any]],
    source_history: list[dict[str, Any]] | None,
) -> ChatSourceHistory:
    return [
        {
            "message_id": msg["message_id"],
            "role": msg["role"],
            "content": msg["content"],
            "sources": list(msg["sources"]),
        }
        for msg in coerce_source_history(visible_history, source_history)
    ]


def _latest_assistant_sources(
    source_history: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [dict(source) for source in latest_assistant_sources(source_history)]


def _reference_panel_from_sources(sources: list[dict[str, Any]] | None) -> tuple[ChatReferenceRows, str]:
    rows = _reference_rows_for_sources(sources)
    if not rows:
        return _empty_reference_rows(), _REFERENCE_NO_SOURCES_STATUS
    return rows, f"Viser {len(rows)} kildehenvisninger."


def _reference_panel_from_history(
    source_history: list[dict[str, Any]] | None,
) -> tuple[ChatReferenceRows, str]:
    sources = _latest_assistant_sources(source_history)
    if not sources:
        return _empty_reference_rows(), _REFERENCE_DEFAULT_STATUS
    return _reference_panel_from_sources(sources)


def _selected_message_index(index: Any) -> int | None:
    if isinstance(index, int):
        return index
    if isinstance(index, (tuple, list)) and index:
        first = index[0]
        if isinstance(first, int):
            return first
    return None


def _chatbot_select_handler(
    source_history: list[dict[str, Any]] | None,
    token: str | None,
    conversation_state: ChatConversationState | dict[str, Any] | None,
    evt: gr.SelectData,
) -> tuple[ChatReferenceRows, str]:
    if getattr(evt, "selected", True) is False:
        return _reference_panel_from_history(source_history)

    selected_index = _selected_message_index(getattr(evt, "index", None))
    if selected_index is None:
        return _empty_reference_rows(), _REFERENCE_DEFAULT_STATUS

    messages = list(source_history or [])
    if selected_index < 0 or selected_index >= len(messages):
        return _empty_reference_rows(), _REFERENCE_DEFAULT_STATUS

    selected_message = messages[selected_index]
    if selected_message.get("role") != "assistant":
        return _empty_reference_rows(), _REFERENCE_USER_SELECTED_STATUS

    if not token:
        return _empty_reference_rows(), "Ikke innlogget."

    conversation_id = normalize_conversation_state(conversation_state).get("conversation_id")
    message_id = str(selected_message.get("message_id") or "").strip()
    if not conversation_id or not message_id:
        return _reference_panel_from_sources(list(selected_message.get("sources") or []))

    sources, err = get_message_sources(token, conversation_id, message_id)
    if err:
        return _empty_reference_rows(), err
    return _reference_panel_from_sources(sources)
