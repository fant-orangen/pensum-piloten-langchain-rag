"""Public chat handler surface, re-exported from focused submodules."""

from src.ui.pages.chat_handlers.bootstrap import (
    _bootstrap_chat_on_route_handler,
    _reset_scope_handler,
    _resolve_course_for_chat_entry,
    _skip_chat_bootstrap_updates,
)
from src.ui.pages.chat_handlers.common import _default_conversation_state
from src.ui.pages.chat_handlers.messaging import _chat_handler, _new_conversation_handler
from src.ui.pages.chat_handlers.sidebar import (
    _conversation_count_text,
    _fetch_conversations,
    _fetch_messages,
    _load_conversation_handler,
    _refresh_handler,
    _refresh_sidebar,
    _selector_choices,
)

__all__ = [
    "_bootstrap_chat_on_route_handler",
    "_chat_handler",
    "_conversation_count_text",
    "_default_conversation_state",
    "_fetch_conversations",
    "_fetch_messages",
    "_load_conversation_handler",
    "_new_conversation_handler",
    "_refresh_handler",
    "_refresh_sidebar",
    "_reset_scope_handler",
    "_resolve_course_for_chat_entry",
    "_selector_choices",
    "_skip_chat_bootstrap_updates",
]
