"""Reference panel and selection helpers for chat handlers."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.ui.pages.chat_handlers.contracts import (
    _REFERENCE_DEFAULT_STATUS,
    _REFERENCE_NO_SOURCES_STATUS,
    _REFERENCE_USER_SELECTED_STATUS,
    ChatReferencePanel,
    ChatSourceHistory,
    ChatVisibleHistory,
)
from src.ui.pages.chat_state import (
    ChatSourceEntry,
    ChatConversationState,
    coerce_source_history,
    empty_reference_panel,
    latest_assistant_sources,
    normalize_conversation_state,
    normalize_source_entry,
    render_reference_panel_for_sources,
    visible_history_from_source_history,
)
from src.ui.services.conversation_service import get_message_sources


def _reference_layout_update(is_open: bool) -> tuple[bool, Any]:
    return is_open, gr.update(visible=is_open)


def _open_reference_layout_handler() -> tuple[bool, Any]:
    return _reference_layout_update(True)


def _close_reference_layout_handler() -> tuple[bool, Any]:
    return _reference_layout_update(False)


def _reference_layout_from_panel_handler(
    panel: str | None,
    status: str | None,
) -> tuple[bool, Any]:
    status_text = str(status or "").strip()
    has_panel = bool(str(panel or "").strip())
    should_open = has_panel and status_text not in {
        _REFERENCE_DEFAULT_STATUS,
        _REFERENCE_NO_SOURCES_STATUS,
        _REFERENCE_USER_SELECTED_STATUS,
    }
    return _reference_layout_update(should_open)


def _empty_reference_panel() -> ChatReferencePanel:
    return empty_reference_panel()


def _normalize_reference_entry(value: Any) -> ChatSourceEntry | None:
    return normalize_source_entry(value)


def _render_reference_panel_for_sources(
    sources: list[dict[str, Any]] | None,
) -> ChatReferencePanel:
    return render_reference_panel_for_sources(sources)


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


def _normalized_source_history(
    source_history: list[dict[str, Any]] | None,
) -> ChatSourceHistory:
    return _coerce_source_history(_visible_history_from_source_history(source_history), source_history)


def _latest_assistant_index(
    source_history: list[dict[str, Any]] | None,
) -> int | None:
    normalized_history = _normalized_source_history(source_history)
    for index in range(len(normalized_history) - 1, -1, -1):
        if normalized_history[index].get("role") == "assistant":
            return index
    return None


def _sources_need_hydration(sources: list[dict[str, Any]] | None) -> bool:
    normalized_sources = [
        normalized
        for source in sources or []
        if (normalized := _normalize_reference_entry(source)) is not None
    ]
    if not normalized_sources:
        return False
    return any(not source["excerpt"].strip() for source in normalized_sources)


def _reference_fallback_status(error_message: str) -> str:
    return f"{error_message} Viser lagrede referanser uten tekstutdrag."


def _hydrate_assistant_sources_at_index(
    source_history: list[dict[str, Any]] | None,
    message_index: int,
    token: str | None,
    conversation_id: str | None,
) -> tuple[ChatSourceHistory, list[dict[str, Any]], str | None]:
    normalized_history = _normalized_source_history(source_history)
    if message_index < 0 or message_index >= len(normalized_history):
        return normalized_history, [], None

    selected_message = dict(normalized_history[message_index])
    if selected_message.get("role") != "assistant":
        return normalized_history, [], None

    normalized_sources = [
        dict(normalized)
        for source in selected_message.get("sources") or []
        if (normalized := _normalize_reference_entry(source)) is not None
    ]
    if not normalized_sources or not _sources_need_hydration(normalized_sources):
        return normalized_history, normalized_sources, None

    message_id = str(selected_message.get("message_id") or "").strip()
    resolved_conversation_id = str(conversation_id or "").strip()
    if not resolved_conversation_id or not message_id:
        return normalized_history, normalized_sources, None

    if not token:
        return normalized_history, normalized_sources, "Ikke innlogget."

    sources, err = get_message_sources(token, resolved_conversation_id, message_id)
    if err:
        return normalized_history, normalized_sources, err

    hydrated_sources = [
        dict(normalized)
        for source in sources
        if (normalized := _normalize_reference_entry(source)) is not None
    ]
    updated_history = list(normalized_history)
    selected_message["sources"] = hydrated_sources
    updated_history[message_index] = selected_message
    return updated_history, hydrated_sources, None


def _hydrate_latest_assistant_sources(
    source_history: list[dict[str, Any]] | None,
    token: str | None,
    conversation_id: str | None,
) -> tuple[ChatSourceHistory, list[dict[str, Any]], str | None]:
    latest_index = _latest_assistant_index(source_history)
    if latest_index is None:
        return _normalized_source_history(source_history), [], None
    return _hydrate_assistant_sources_at_index(source_history, latest_index, token, conversation_id)


def _reference_panel_from_sources(
    sources: list[dict[str, Any]] | None,
) -> tuple[ChatReferencePanel, str]:
    count = len([source for source in sources or [] if normalize_source_entry(source) is not None])
    if count == 0:
        return _empty_reference_panel(), _REFERENCE_NO_SOURCES_STATUS
    return _render_reference_panel_for_sources(sources), f"Viser {count} kildehenvisninger."


def _reference_panel_from_history(
    source_history: list[dict[str, Any]] | None,
) -> tuple[ChatReferencePanel, str]:
    latest_index = _latest_assistant_index(source_history)
    if latest_index is None:
        return _empty_reference_panel(), _REFERENCE_DEFAULT_STATUS
    sources = _normalized_source_history(source_history)[latest_index].get("sources") or []
    if not sources:
        return _empty_reference_panel(), _REFERENCE_NO_SOURCES_STATUS
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
) -> tuple[ChatSourceHistory, ChatReferencePanel, str]:
    if getattr(evt, "selected", True) is False:
        panel, status = _reference_panel_from_history(source_history)
        return _normalized_source_history(source_history), panel, status

    selected_index = _selected_message_index(getattr(evt, "index", None))
    if selected_index is None:
        return _normalized_source_history(source_history), _empty_reference_panel(), _REFERENCE_DEFAULT_STATUS

    messages = _normalized_source_history(source_history)
    if selected_index < 0 or selected_index >= len(messages):
        return messages, _empty_reference_panel(), _REFERENCE_DEFAULT_STATUS

    selected_message = messages[selected_index]
    if selected_message.get("role") != "assistant":
        return messages, _empty_reference_panel(), _REFERENCE_USER_SELECTED_STATUS

    conversation_id = normalize_conversation_state(conversation_state).get("conversation_id")
    hydrated_history, sources, err = _hydrate_assistant_sources_at_index(
        messages,
        selected_index,
        token,
        conversation_id,
    )
    if err:
        if sources:
            panel, _status = _reference_panel_from_sources(sources)
            return hydrated_history, panel, _reference_fallback_status(err)
        return hydrated_history, _empty_reference_panel(), err
    panel, status = _reference_panel_from_sources(sources)
    return hydrated_history, panel, status
