"""Conversation service — wraps /conversations/* API endpoints."""

from __future__ import annotations

from typing import Any

from src.ui.services.api_client import ApiError, ApiUnauthorizedError, get, post

_EXCERPT_PREVIEW_CHARS = 220


def _normalize_excerpt(value: Any) -> str:
    """Return a compact one-line preview for display in the references panel."""
    text = " ".join(str(value or "").split())
    if len(text) <= _EXCERPT_PREVIEW_CHARS:
        return text
    return text[: _EXCERPT_PREVIEW_CHARS - 3].rstrip() + "..."


def _extract_document(value: dict[str, Any]) -> str:
    for key in ("document", "source_file", "filename", "file", "source", "name"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return "Ukjent dokument"


def _extract_page(value: dict[str, Any]) -> str:
    page = value.get("page")
    if page is None:
        return ""
    if isinstance(page, str):
        return page.strip()
    return str(page)


def _extract_excerpt(value: dict[str, Any]) -> str:
    for key in ("excerpt", "text", "content", "chunk", "snippet"):
        candidate = value.get(key)
        if isinstance(candidate, str) and candidate.strip():
            return _normalize_excerpt(candidate)
    return ""


def normalize_sources_payload(value: Any) -> list[dict[str, str]]:
    """Normalize backend source payloads to a frontend-safe shape."""
    if isinstance(value, str):
        document = value.strip()
        return [{"document": document or "Ukjent dokument", "page": "", "excerpt": ""}]
    if isinstance(value, dict):
        return [
            {
                "document": _extract_document(value),
                "page": _extract_page(value),
                "excerpt": _extract_excerpt(value),
            }
        ]
    if not isinstance(value, list):
        return []

    normalized: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, str):
            document = item.strip()
            normalized.append(
                {"document": document or "Ukjent dokument", "page": "", "excerpt": ""}
            )
            continue
        if isinstance(item, dict):
            normalized.append(
                {
                    "document": _extract_document(item),
                    "page": _extract_page(item),
                    "excerpt": _extract_excerpt(item),
                }
            )
    return normalized


def _normalize_message_payload(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    normalized = dict(value)
    normalized["sources"] = normalize_sources_payload(value.get("sources"))
    return normalized


def list_conversations(
    token: str,
    *,
    page: int = 1,
    page_size: int = 20,
    course_id: str | None = None,
) -> tuple[list[dict[str, Any]], int, str]:
    """Fetch a page of conversations for the authenticated user.

    Returns:
        (conversations, total, error_message)

        On success, conversations is a list of dicts with keys:
            id, course_id, title, created_at, updated_at
        total is the total number of conversations.
        On failure, conversations is empty and error_message is non-empty.
    """
    try:
        path = f"/conversations?page={page}&page_size={page_size}"
        if course_id:
            path += f"&course_id={course_id}"
        data = get(path, token=token)
    except ApiUnauthorizedError:
        return [], 0, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        return [], 0, f"Kunne ikke hente samtaler: {exc.detail}"
    except Exception as exc:
        return [], 0, f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, dict):
        return [], 0, "Uventet svar fra serveren."

    items = data.get("items", [])
    total = data.get("total", 0)
    if not isinstance(items, list):
        return [], 0, "Uventet svar fra serveren."
    return items, int(total), ""


def get_messages(
    token: str,
    conversation_id: str,
    *,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[dict[str, Any]], int, str]:
    """Fetch a page of messages for a conversation, newest first.

    The API returns messages newest-first; callers should reverse the list
    to display in chronological order.

    Returns:
        (messages, total, error_message)

        On success, messages is a list of dicts with keys:
            id, conversation_id, role, content, sources, created_at
    """
    try:
        data = get(
            f"/conversations/{conversation_id}/messages?page={page}&page_size={page_size}",
            token=token,
        )
    except ApiUnauthorizedError:
        return [], 0, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return [], 0, "Du har ikke tilgang til denne samtalen."
        return [], 0, f"Kunne ikke hente meldinger: {exc.detail}"
    except Exception as exc:
        return [], 0, f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, dict):
        return [], 0, "Uventet svar fra serveren."

    items = data.get("items", [])
    total = data.get("total", 0)
    if not isinstance(items, list):
        return [], 0, "Uventet svar fra serveren."
    normalized_items = [
        normalized
        for item in items
        if (normalized := _normalize_message_payload(item)) is not None
    ]
    return normalized_items, int(total), ""


def get_message_sources(
    token: str,
    conversation_id: str,
    message_id: str,
) -> tuple[list[dict[str, str]], str]:
    """Fetch resolved source chunks for a specific message."""
    try:
        data = get(
            f"/conversations/{conversation_id}/messages/{message_id}/sources",
            token=token,
        )
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return [], "Du har ikke tilgang til denne samtalen."
        if exc.status == 404:
            return [], "Meldingen ble ikke funnet."
        return [], f"Kunne ikke hente kilder: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    return normalize_sources_payload(data), ""


def create_conversation(
    token: str,
    course_id: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Start a new conversation in a course.

    Returns:
        (success, message, conversation_data)

        On success, conversation_data is a dict with keys:
            id, course_id, title, created_at, updated_at
    """
    try:
        data = post("/conversations", {"course_id": course_id}, token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 403:
            return False, "Du er ikke registrert i dette faget.", None
        if exc.status == 404:
            return False, "Faget ble ikke funnet.", None
        return False, f"Kunne ikke opprette samtale: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "Ny samtale opprettet.", data


def send_message(
    token: str,
    conversation_id: str,
    content: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Send a message to a conversation and receive the AI response.

    The backend persists both the human message and the AI response, and
    returns the AI message.

    Returns:
        (success, error_message, ai_message_data)

        On success, ai_message_data is a dict with keys:
            id, conversation_id, role, content, sources, created_at
    """
    try:
        data = post(
            f"/conversations/{conversation_id}/messages",
            {"content": content},
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 403:
            return False, "Du har ikke tilgang til denne samtalen.", None
        if exc.status == 404:
            return False, "Samtalen ble ikke funnet.", None
        if exc.status == 400:
            return False, f"Feil: {exc.detail}", None
        return False, f"Feil ved sending av melding: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    normalized = _normalize_message_payload(data)
    if normalized is None:
        return False, "Uventet svar fra serveren.", None
    return True, "", normalized
