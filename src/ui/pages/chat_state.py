"""Typed chat-state contracts and normalization helpers for the chat UI."""

from __future__ import annotations

from html import escape
from typing import Any, Literal, Mapping, TypedDict

ChatRole = Literal["user", "assistant"]


class ChatConversationState(TypedDict):
    conversation_id: str | None
    title: str | None
    course_id: str | None


class ChatSourceEntry(TypedDict):
    document: str
    page: str
    excerpt: str


class ChatTurn(TypedDict):
    message_id: str | None
    role: ChatRole
    content: str
    sources: list[ChatSourceEntry]


class ChatVisibleTurn(TypedDict):
    role: ChatRole
    content: str


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


def empty_reference_panel() -> str:
    return ""


def normalize_source_entry(value: Any) -> ChatSourceEntry | None:
    if not isinstance(value, dict):
        return None
    document = str(value.get("document") or "Ukjent dokument").strip() or "Ukjent dokument"
    page = str(value.get("page") or "").strip()
    excerpt = str(value.get("excerpt") or "").strip()
    return {"document": document, "page": page, "excerpt": excerpt}


def render_reference_panel_for_sources(sources: list[dict[str, Any]] | None) -> str:
    normalized_sources: list[ChatSourceEntry] = []
    for source in sources or []:
        normalized = normalize_source_entry(source)
        if normalized is not None:
            normalized_sources.append(normalized)

    if not normalized_sources:
        return empty_reference_panel()

    entries: list[str] = []
    for index, source in enumerate(normalized_sources):
        document = escape(source["document"] or "Ukjent dokument")
        page = escape(source["page"] or "Ukjent")
        excerpt = escape(source["excerpt"] or "Ingen tekst tilgjengelig.").replace("\n", "<br>")
        separator = (
            '<hr style="border: 0; border-top: 1px solid #d1d5db; margin: 0.75rem 0 0;">'
            if index < len(normalized_sources) - 1
            else ""
        )
        entries.append(
            "".join(
                [
                    '<div class="chat-reference-entry" '
                    'style="display: flex; flex-direction: column; gap: 0.35rem;">',
                    f'<div><strong>Dokument:</strong> {document}</div>',
                    f'<div><strong>Side:</strong> {page}</div>',
                    f'<div><strong>Tekst:</strong> {excerpt}</div>',
                    separator,
                    "</div>",
                ]
            )
        )

    return (
        '<div class="chat-reference-panel" '
        'style="display: flex; flex-direction: column; gap: 0.75rem;">'
        + "".join(entries)
        + "</div>"
    )


def _role_from_value(value: Any) -> ChatRole | None:
    role = str(value or "").strip()
    if role == "user":
        return "user"
    if role == "assistant":
        return "assistant"
    return None


def _normalize_sources(value: Any) -> list[ChatSourceEntry]:
    if not isinstance(value, list):
        return []
    normalized: list[ChatSourceEntry] = []
    for source in value:
        entry = normalize_source_entry(source)
        if entry is not None:
            normalized.append(entry)
    return normalized


def visible_history_from_source_history(
    source_history: list[dict[str, Any]] | None,
) -> list[ChatVisibleTurn]:
    visible: list[ChatVisibleTurn] = []
    for msg in source_history or []:
        if not isinstance(msg, dict):
            continue
        role = _role_from_value(msg.get("role"))
        if role is None:
            continue
        visible.append({"role": role, "content": str(msg.get("content", ""))})
    return visible


def coerce_source_history(
    visible_history: list[dict[str, Any]],
    source_history: list[dict[str, Any]] | None,
) -> list[ChatTurn]:
    if source_history:
        normalized: list[ChatTurn] = []
        for msg in source_history:
            if not isinstance(msg, dict):
                continue
            role = _role_from_value(msg.get("role"))
            if role is None:
                continue
            normalized.append(
                {
                    "message_id": _clean_optional_text(msg.get("message_id")),
                    "role": role,
                    "content": str(msg.get("content", "")),
                    "sources": _normalize_sources(msg.get("sources")),
                }
            )
        return normalized

    fallback: list[ChatTurn] = []
    for msg in visible_history:
        if not isinstance(msg, dict):
            continue
        role = _role_from_value(msg.get("role"))
        if role is None:
            continue
        fallback.append(
            {
                "message_id": None,
                "role": role,
                "content": str(msg.get("content", "")),
                "sources": [],
            }
        )
    return fallback


def latest_assistant_sources(
    source_history: list[dict[str, Any]] | None,
) -> list[ChatSourceEntry]:
    for msg in reversed(source_history or []):
        if not isinstance(msg, dict):
            continue
        role = _role_from_value(msg.get("role"))
        if role != "assistant":
            continue
        return _normalize_sources(msg.get("sources"))
    return []
