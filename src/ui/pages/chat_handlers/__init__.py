"""Public chat handler surface, re-exported from focused submodules."""

from src.ui.pages.chat_handlers.bootstrap import (
    _bootstrap_chat_on_route_handler,
    _reset_scope_handler,
    _resolve_course_for_chat_entry,
    _skip_chat_bootstrap_updates,
)
from src.ui.pages.chat_handlers.common import (
    _default_conversation_state,
    _get_user_system_prompt_mode,
    _mode_label,
)
from src.ui.pages.chat_handlers.contracts import (
    _MODE_CHOICES,
    _REFERENCE_DEFAULT_STATUS,
)
from src.ui.pages.chat_handlers.messaging import _chat_handler, _new_conversation_handler
from src.ui.pages.chat_handlers.references import (
    _chatbot_select_handler,
    _coerce_source_history,
    _empty_reference_panel,
    _latest_assistant_sources,
    _normalize_reference_entry,
    _reference_panel_from_history,
    _reference_panel_from_sources,
    _render_reference_panel_for_sources,
    _selected_message_index,
    _visible_history_from_source_history,
)
from src.ui.pages.chat_handlers.sidebar import (
    _conversation_count_text,
    _fetch_conversations,
    _fetch_messages,
    _load_conversation_handler,
    _open_conversation_text,
    _refresh_handler,
    _refresh_sidebar,
    _selector_choices,
)

__all__ = [
    "_MODE_CHOICES",
    "_REFERENCE_DEFAULT_STATUS",
    "_bootstrap_chat_on_route_handler",
    "_chat_handler",
    "_chatbot_select_handler",
    "_coerce_source_history",
    "_conversation_count_text",
    "_default_conversation_state",
    "_empty_reference_panel",
    "_fetch_conversations",
    "_fetch_messages",
    "_get_user_system_prompt_mode",
    "_latest_assistant_sources",
    "_load_conversation_handler",
    "_mode_label",
    "_new_conversation_handler",
    "_normalize_reference_entry",
    "_open_conversation_text",
    "_reference_panel_from_history",
    "_reference_panel_from_sources",
    "_render_reference_panel_for_sources",
    "_refresh_handler",
    "_refresh_sidebar",
    "_reset_scope_handler",
    "_resolve_course_for_chat_entry",
    "_selected_message_index",
    "_selector_choices",
    "_skip_chat_bootstrap_updates",
    "_visible_history_from_source_history",
]
