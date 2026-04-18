"""Common chat helper functions shared across handler modules."""

from __future__ import annotations
from src.ui.pages.chat_state import ChatConversationState, default_conversation_state


def _default_conversation_state() -> ChatConversationState:
    """Return an empty conversation state dict with all fields set to None."""
    return default_conversation_state()
