"""Common chat helper functions shared across handler modules."""

from __future__ import annotations

from src.ui.pages.chat_handlers.contracts import _MODE_LABELS
from src.ui.pages.chat_state import ChatConversationState, default_conversation_state


def _default_conversation_state() -> ChatConversationState:
    """Return an empty conversation state dict with all fields set to None."""
    return default_conversation_state()


def _mode_label(mode: int) -> str:
    return _MODE_LABELS.get(mode, "valgt modus")


def _get_user_system_prompt_mode(token: str) -> tuple[int | None, str]:
    from src.ui.services.auth_service import current_user

    ok, message, user = current_user(token)
    if not ok or not isinstance(user, dict):
        return None, message or "Kunne ikke hente aktiv standardmodus."

    raw_mode = user.get("system_prompt_mode")
    if isinstance(raw_mode, int) and raw_mode in {1, 2, 3}:
        return raw_mode, ""
    return None, "Ugyldig standardmodus mottatt fra serveren."
