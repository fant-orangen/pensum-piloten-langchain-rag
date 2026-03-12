"""Chat UI orchestration helpers built on top of UI service clients."""

from __future__ import annotations

from textwrap import shorten
from typing import Any, TypedDict


class ChatSidebarModel(TypedDict):
    choices: list[tuple[str, str]]
    selected_id: str | None
    count: int
    status_text: str


def resolve_course_for_chat_entry(
    token: str,
    course_id_state: str | None,
    *,
    no_course_status: str,
    auto_course_status: str,
) -> tuple[str | None, str, bool]:
    resolved_course_id = (course_id_state or "").strip()
    if resolved_course_id:
        return resolved_course_id, "", False

    from src.ui.services.course_service import list_courses

    courses, err = list_courses(token)
    if err:
        return None, err, False

    first_course = next(
        (
            course
            for course in courses
            if isinstance(course, dict) and str(course.get("id", "")).strip()
        ),
        None,
    )
    if first_course is None:
        return None, no_course_status, False

    return str(first_course.get("id", "")).strip(), auto_course_status, True


def selector_choices(conversations: list[dict[str, Any]], *, title_width: int = 60) -> list[tuple[str, str]]:
    choices = []
    for conv in conversations:
        title = conv.get("title") or "Samtale"
        updated_at = conv.get("updated_at", "")
        label = shorten(f"{title} — {updated_at[:16]}", width=title_width, placeholder="…")
        choices.append((label, str(conv.get("id", ""))))
    return choices


def fetch_conversations(
    token: str,
    course_id: str | None,
    *,
    no_course_status: str,
) -> tuple[list[dict[str, Any]], str]:
    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        return [], no_course_status

    from src.ui.services.conversation_service import list_conversations

    items, _total, err = list_conversations(token, course_id=resolved_course_id)
    return items, err


def fetch_messages(conversation_token: str, conversation_id: str) -> tuple[list[dict[str, Any]], str]:
    from src.ui.services.conversation_service import get_messages

    all_messages: list[dict[str, Any]] = []
    page = 1
    while True:
        items, total, err = get_messages(
            conversation_token,
            conversation_id,
            page=page,
            page_size=50,
        )
        if err:
            return [], err
        all_messages.extend(items)
        if len(all_messages) >= total or not items:
            break
        page += 1

    all_messages.reverse()
    history: list[dict[str, Any]] = []
    for msg in all_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "human":
            history.append(
                {
                    "message_id": str(msg.get("id", "")).strip() or None,
                    "role": "user",
                    "content": content,
                    "sources": [],
                }
            )
        elif role == "ai":
            history.append(
                {
                    "message_id": str(msg.get("id", "")).strip() or None,
                    "role": "assistant",
                    "content": content,
                    "sources": list(msg.get("sources") or []),
                }
            )
    return history, ""


def build_sidebar_model(
    token: str,
    *,
    course_id: str | None,
    selected_id: str | None = None,
    status_message: str = "",
    no_course_status: str,
) -> ChatSidebarModel:
    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        status_text = status_message or no_course_status
        return {
            "choices": [],
            "selected_id": None,
            "count": 0,
            "status_text": status_text,
        }

    conversations, err = fetch_conversations(token, resolved_course_id, no_course_status=no_course_status)
    if err:
        status_message = err

    choices = selector_choices(conversations)
    resolved_value = selected_id if any(v == selected_id for _, v in choices) else None

    selected_conv = next(
        (c for c in conversations if str(c.get("id", "")) == resolved_value),
        None,
    )

    return {
        "choices": choices,
        "selected_id": resolved_value,
        "count": len(conversations),
        "status_text": status_message,
    }


def create_chat_conversation(
    token: str,
    course_id: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    from src.ui.services.conversation_service import create_conversation

    return create_conversation(token, course_id)


def send_chat_message(
    token: str,
    conversation_id: str,
    content: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    from src.ui.services.conversation_service import send_message

    return send_message(token, conversation_id, content)
