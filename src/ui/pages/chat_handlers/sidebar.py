"""Sidebar and conversation-loading chat handlers."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.ui.pages.chat_handlers.common import _default_conversation_state
from src.ui.pages.chat_handlers.contracts import (
    _NO_COURSE_STATUS,
    _OUT_OF_SCOPE_STATUS,
    _REFERENCE_DEFAULT_STATUS,
    ChatOutputs,
    ChatRefreshOutputs,
)
from src.ui.pages.chat_handlers.references import (
    _empty_reference_panel,
    _reference_panel_from_history,
    _visible_history_from_source_history,
)
from src.ui.pages.chat_state import ChatConversationState, normalize_conversation_state
from src.ui.services.chat_orchestration_service import (
    build_sidebar_model,
    fetch_conversations,
    fetch_messages,
    selector_choices as selector_choices_service,
)


def _open_conversation_text(title: str | None) -> str:
    """Format the label shown above the chat area for the currently open conversation."""
    return f"Åpen samtale: {title or 'Ingen'}"


def _conversation_count_text(count: int) -> str:
    """Return a Norwegian summary string for the number of conversations found."""
    if count == 0:
        return "Ingen tidligere samtaler funnet."
    if count == 1:
        return "1 samtale funnet."
    return f"{count} samtaler funnet."


def _selector_choices(conversations: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Convert a list of conversation dicts into (label, id) pairs for the selector."""
    return selector_choices_service(conversations)


def _fetch_conversations(token: str, course_id: str | None = None) -> tuple[list[dict[str, Any]], str]:
    """Return (conversations, error_message). Conversations are ordered newest-first."""
    return fetch_conversations(token, course_id, no_course_status=_NO_COURSE_STATUS)


def _fetch_messages(token: str, conversation_id: str) -> tuple[list[dict[str, Any]], str]:
    """Return (messages_in_chronological_order, error_message)."""
    return fetch_messages(token, conversation_id)


def _refresh_sidebar(
    token: str,
    selected_id: str | None = None,
    *,
    course_id: str | None = None,
    status_message: str = "",
) -> tuple[Any, str, str, str]:
    """Fetch sidebar data and return selector/count/status/open label updates."""
    model = build_sidebar_model(
        token,
        course_id=course_id,
        selected_id=selected_id,
        status_message=status_message,
        no_course_status=_NO_COURSE_STATUS,
    )

    return (
        gr.update(choices=model["choices"], value=model["selected_id"]),
        _conversation_count_text(model["count"]),
        model["status_text"],
        _open_conversation_text(model["open_title"]),
    )


def _load_conversation_handler(
    conversation_id: str | None,
    token: str | None,
    course_id: str | None,
) -> ChatOutputs:
    """Load message history for the selected conversation and update the chat UI."""
    if not token:
        return (
            "",
            [],
            "Ikke innlogget.",
            _default_conversation_state(),
            gr.update(),
            "",
            _open_conversation_text(None),
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id,
            status_message=_NO_COURSE_STATUS,
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    if not conversation_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message="Ingen samtale valgt."
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    conversations, err = _fetch_conversations(token, resolved_course_id)
    if err:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message=err
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    selected_conv = next(
        (c for c in conversations if str(c.get("id", "")) == conversation_id),
        None,
    )
    if selected_conv is None:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id,
            status_message=_OUT_OF_SCOPE_STATUS,
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    source_history, err = _fetch_messages(token, conversation_id)
    if err:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message=err
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    title = selected_conv.get("title") if selected_conv else "Samtale"
    conv_state: ChatConversationState = {
        "conversation_id": conversation_id,
        "title": title,
        "course_id": str(selected_conv.get("course_id", "")) if selected_conv else None,
    }

    selector_update, count_text, status_text, open_text = _refresh_sidebar(
        token,
        conversation_id,
        course_id=course_id,
        status_message=f"Lastet samtale: {title}.",
    )
    reference_panel, reference_status = _reference_panel_from_history(source_history)
    return (
        "",
        _visible_history_from_source_history(source_history),
        status_text,
        conv_state,
        selector_update,
        count_text,
        open_text,
        source_history,
        reference_panel,
        reference_status,
    )


def _refresh_handler(
    conversation_state: ChatConversationState | dict[str, Any] | None,
    source_history: list[dict[str, Any]] | None,
    token: str | None,
    course_id_state: str | None,
) -> ChatRefreshOutputs:
    """Re-fetch the conversation list and return updated sidebar components."""
    current_state = normalize_conversation_state(conversation_state)

    if not token:
        return (
            gr.update(choices=[], value=None),
            "",
            "Ikke innlogget.",
            _open_conversation_text(None),
            _default_conversation_state(),
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    if not (course_id_state or "").strip():
        return (
            gr.update(choices=[], value=None),
            _conversation_count_text(0),
            _NO_COURSE_STATUS,
            _open_conversation_text(None),
            _default_conversation_state(),
            [],
            _empty_reference_panel(),
            _REFERENCE_DEFAULT_STATUS,
        )

    active_course_id = str(course_id_state or "").strip()
    conv_id = str(current_state.get("conversation_id") or "").strip()
    conversations, err = _fetch_conversations(token, active_course_id)
    choices = _selector_choices(conversations)
    resolved_value = conv_id if conv_id and any(item[1] == conv_id for item in choices) else None
    selected_conv = next(
        (item for item in conversations if str(item.get("id", "")) == resolved_value),
        None,
    )
    next_state: ChatConversationState = {
        "conversation_id": resolved_value,
        "title": selected_conv.get("title") if selected_conv else None,
        "course_id": active_course_id if selected_conv else None,
    }
    next_source_history = list(source_history or []) if resolved_value else []
    reference_panel, reference_status = _reference_panel_from_history(next_source_history)
    status_text = err or "Samtalelisten er oppdatert."
    return (
        gr.update(choices=choices, value=resolved_value),
        _conversation_count_text(len(conversations)),
        status_text,
        _open_conversation_text(next_state.get("title")),
        next_state if resolved_value else _default_conversation_state(),
        next_source_history,
        reference_panel if resolved_value else _empty_reference_panel(),
        reference_status if resolved_value else _REFERENCE_DEFAULT_STATUS,
    )
