"""Shared contracts and constants for chat handlers."""

from __future__ import annotations

from typing import Any, TypeAlias

from src.ui.pages.chat_state import ChatConversationState

_MODE_CHOICES = [
    ("Socratic mode", 1),
    ("Direct mode", 2),
    ("Example mode", 3),
]
_MODE_LABELS = {value: label for label, value in _MODE_CHOICES}

_NO_COURSE_STATUS = "Velg et fag før du bruker chat."
_SCOPE_CHANGED_STATUS = "Fagkonteksten ble endret. Velg eller opprett en ny samtale."
_OUT_OF_SCOPE_STATUS = "Samtalen er ikke i aktivt fag. Velg eller opprett en ny samtale."
_AUTO_COURSE_STATUS = "Fag valgt automatisk. Velg eller opprett en samtale først."

_REFERENCE_HEADERS = ["Dokument", "Side", "Utdrag"]
_REFERENCE_DEFAULT_STATUS = "Velg et tutorsvar for å se kilder."
_REFERENCE_NO_SOURCES_STATUS = "Ingen kilder registrert for dette svaret."
_REFERENCE_USER_SELECTED_STATUS = "Kilder vises bare for tutorsvar."

ChatVisibleHistory: TypeAlias = list[dict[str, str]]
ChatSourceHistory: TypeAlias = list[dict[str, Any]]
ChatReferenceRows: TypeAlias = list[list[str]]

ChatOutputs: TypeAlias = tuple[
    str,
    ChatVisibleHistory,
    str,
    ChatConversationState,
    Any,
    str,
    str,
    ChatSourceHistory,
    ChatReferenceRows,
    str,
]

ChatBootstrapOutputs: TypeAlias = tuple[
    str,
    ChatVisibleHistory,
    str,
    ChatConversationState,
    Any,
    str,
    str,
    ChatSourceHistory,
    ChatReferenceRows,
    str,
    str | None,
]

ChatRefreshOutputs: TypeAlias = tuple[
    Any,
    str,
    str,
    str,
    ChatConversationState,
    ChatSourceHistory,
    ChatReferenceRows,
    str,
]
