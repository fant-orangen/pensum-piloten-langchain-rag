"""Shared contracts and constants for chat handlers."""

from __future__ import annotations

from typing import Any, TypeAlias

from src.ui.pages.chat_state import ChatConversationState

_NO_COURSE_STATUS = "Velg et fag før du bruker chat."
_SCOPE_CHANGED_STATUS = "Fagkonteksten ble endret. Velg eller opprett en ny samtale."
_OUT_OF_SCOPE_STATUS = "Samtalen er ikke i aktivt fag. Velg eller opprett en ny samtale."
_AUTO_COURSE_STATUS = "Fag valgt automatisk. Velg eller opprett en samtale først."

ChatVisibleHistory: TypeAlias = list[dict[str, str]]

ChatOutputs: TypeAlias = tuple[
    str,
    ChatVisibleHistory,
    str,
    ChatConversationState,
    Any,
    str,
]

ChatBootstrapOutputs: TypeAlias = tuple[
    str,
    ChatVisibleHistory,
    str,
    ChatConversationState,
    Any,
    str,
    str | None,
]

ChatRefreshOutputs: TypeAlias = tuple[
    Any,
    str,
    str,
    ChatConversationState,
]
