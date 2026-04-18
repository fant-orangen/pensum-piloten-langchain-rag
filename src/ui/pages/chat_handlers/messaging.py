"""Conversation creation and message-send handlers for chat UI."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.ui.pages.chat_handlers.common import (
    _default_conversation_state,
)
from src.ui.pages.chat_handlers.contracts import (
    _NO_COURSE_STATUS,
    _OUT_OF_SCOPE_STATUS,
    ChatOutputs,
)
from src.ui.pages.chat_handlers.sidebar import _refresh_sidebar
from src.ui.pages.chat_state import ChatConversationState, normalize_conversation_state
from src.ui.services.chat_orchestration_service import create_chat_conversation, send_chat_message


def _new_conversation_handler(
    token: str | None,
    course_id_state: str | None,
) -> ChatOutputs:
    """Create a new conversation for the resolved course ID and refresh the sidebar."""
    if not token:
        return (
            "",
            [],
            "Ikke innlogget.",
            _default_conversation_state(),
            gr.update(),
            "",
        )

    course_id = (course_id_state or "").strip()
    if not course_id:
        selector_update, count_text, status_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message=_NO_COURSE_STATUS
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
        )

    success, message, conv_data = create_chat_conversation(token, course_id)
    if not success or conv_data is None:
        selector_update, count_text, status_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message=message
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
        )

    conv_id = str(conv_data.get("id", ""))
    title = conv_data.get("title") or "Ny samtale"
    conv_state: ChatConversationState = {
        "conversation_id": conv_id,
        "title": title,
        "course_id": course_id,
    }
    status_message = "Ny samtale opprettet."

    selector_update, count_text, status_text = _refresh_sidebar(
        token,
        conv_id,
        course_id=course_id_state,
        status_message=status_message,
    )
    return (
        "",
        [],
        status_text,
        conv_state,
        selector_update,
        count_text,
    )


def _chat_handler(
    user_message: str,
    history: list[dict[str, Any]] | None,
    conversation_state: ChatConversationState | dict[str, Any] | None,
    token: str | None,
    course_id_state: str | None,
) -> ChatOutputs:
    """Send a user message to the backend and append both turns to chat history."""
    visible_history = [
        {"role": str(msg.get("role", "")), "content": str(msg.get("content", ""))}
        for msg in (history or [])
        if isinstance(msg, dict) and msg.get("role") in {"user", "assistant"}
    ]
    text = (user_message or "").strip()
    current_state = normalize_conversation_state(conversation_state)

    if not token:
        return (
            "",
            visible_history,
            "Ikke innlogget.",
            current_state,
            gr.update(),
            "",
        )

    if not (course_id_state or "").strip():
        selector_update, count_text, status_text = _refresh_sidebar(
            token,
            course_id=course_id_state,
            status_message=_NO_COURSE_STATUS,
        )
        return (
            "",
            visible_history,
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
        )

    active_course_id = str(course_id_state or "").strip()
    if not text:
        conv_id = current_state.get("conversation_id")
        selector_update, count_text, status_text = _refresh_sidebar(
            token,
            conv_id,
            course_id=course_id_state,
        )
        return (
            "",
            visible_history,
            status_text,
            current_state,
            selector_update,
            count_text,
        )

    conv_id = current_state.get("conversation_id")
    conv_course_id = str(current_state.get("course_id") or "").strip()
    if conv_id and conv_course_id != active_course_id:
        selector_update, count_text, status_text = _refresh_sidebar(
            token,
            course_id=course_id_state,
            status_message=_OUT_OF_SCOPE_STATUS,
        )
        return (
            "",
            visible_history,
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
        )

    if not conv_id:
        # Auto-create the first conversation so the user's first send is actionable.
        created, created_message, conv_data = create_chat_conversation(token, active_course_id)
        if not created or conv_data is None:
            selector_update, count_text, status_text = _refresh_sidebar(
                token,
                course_id=course_id_state,
                status_message=created_message,
            )
            return (
                "",
                visible_history,
                status_text,
                current_state,
                selector_update,
                count_text,
            )
        conv_id = str(conv_data.get("id", "")).strip()
        if not conv_id:
            selector_update, count_text, status_text = _refresh_sidebar(
                token,
                course_id=course_id_state,
                status_message="Kunne ikke opprette ny samtale.",
            )
            return (
                "",
                visible_history,
                status_text,
                current_state,
                selector_update,
                count_text,
            )
        current_state = {
            "conversation_id": conv_id,
            "title": conv_data.get("title") or "Ny samtale",
            "course_id": active_course_id,
        }

    success, err, ai_msg_data = send_chat_message(token, conv_id, text)
    if not success or ai_msg_data is None:
        selector_update, count_text, status_text = _refresh_sidebar(
            token,
            conv_id,
            course_id=course_id_state,
            status_message=err,
        )
        return (
            "",
            visible_history,
            status_text,
            current_state,
            selector_update,
            count_text,
        )

    ai_content = ai_msg_data.get("content", "")
    updated_history = visible_history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": ai_content},
    ]

    selector_update, count_text, status_text = _refresh_sidebar(
        token,
        conv_id,
        course_id=course_id_state,
    )
    return (
        "",
        updated_history,
        status_text,
        current_state,
        selector_update,
        count_text,
    )
