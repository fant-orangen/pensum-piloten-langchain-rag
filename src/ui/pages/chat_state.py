"""Typed chat-state contracts and normalization helpers for the chat UI."""

from __future__ import annotations

from typing import Any, Mapping, TypedDict


def _clean_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def default_conversation_state() -> ChatConversationState:
    return {
        "conversation_id": None,
        "title": None,
        "course_id": None,
    }


def normalize_conversation_state(value: Mapping[str, Any] | None) -> ChatConversationState:
    if value is None:
        return default_conversation_state()

    return {
        "conversation_id": _clean_optional_text(value.get("conversation_id")),
        "title": _clean_optional_text(value.get("title")),
        "course_id": _clean_optional_text(value.get("course_id")),
    }


