"""Route/bootstrap/reset handlers for chat page scope changes."""

from __future__ import annotations

import gradio as gr

from src.ui.pages.chat_handlers.common import _default_conversation_state
from src.ui.pages.chat_handlers.contracts import (
    _AUTO_COURSE_STATUS,
    _NO_COURSE_STATUS,
    _SCOPE_CHANGED_STATUS,
    ChatBootstrapOutputs,
    ChatOutputs,
)
from src.ui.pages.chat_handlers.sidebar import (
    _conversation_count_text,
    _refresh_sidebar,
)
from src.ui.router import ROUTE_CHAT
from src.ui.services.chat_orchestration_service import (
    resolve_course_for_chat_entry as resolve_course_for_chat_entry_service,
)


def _resolve_course_for_chat_entry(
    token: str,
    course_id_state: str | None,
) -> tuple[str | None, str, bool]:
    return resolve_course_for_chat_entry_service(
        token,
        course_id_state,
        no_course_status=_NO_COURSE_STATUS,
        auto_course_status=_AUTO_COURSE_STATUS,
    )


def _skip_chat_bootstrap_updates() -> ChatBootstrapOutputs:
    skip = gr.skip()
    return (
        skip,
        skip,
        skip,
        skip,
        skip,
        skip,
        skip,
    )


def _bootstrap_chat_on_route_handler(
    route: str | None,
    token: str | None,
    course_id_state: str | None,
) -> ChatBootstrapOutputs:
    # Route-based bootstrap is required because token/course values may remain
    # unchanged across page navigation, which means .change handlers will not fire.
    if route != ROUTE_CHAT:
        return _skip_chat_bootstrap_updates()

    if not token:
        return (
            "",
            [],
            "Ikke innlogget.",
            _default_conversation_state(),
            gr.update(choices=[], value=None),
            _conversation_count_text(0),
            None,
        )

    resolved_course_id, resolve_status, _auto_selected = _resolve_course_for_chat_entry(
        token,
        course_id_state,
    )
    if not resolved_course_id:
        return (
            "",
            [],
            resolve_status or _NO_COURSE_STATUS,
            _default_conversation_state(),
            gr.update(choices=[], value=None),
            _conversation_count_text(0),
            None,
        )

    status_seed = resolve_status or "Velg eller opprett en samtale først."
    selector_update, count_text, status_text = _refresh_sidebar(
        token,
        course_id=resolved_course_id,
        status_message=status_seed,
    )
    return (
        "",
        [],
        status_text,
        _default_conversation_state(),
        selector_update,
        count_text,
        resolved_course_id,
    )


def _reset_scope_handler(
    token: str | None,
    course_id_state: str | None,
) -> ChatOutputs:
    """Reset local chat state when auth/course scope changes."""
    if not token:
        status_text = "Ikke innlogget."
    elif not (course_id_state or "").strip():
        status_text = _NO_COURSE_STATUS
    else:
        status_text = _SCOPE_CHANGED_STATUS
    return (
        "",
        [],
        status_text,
        _default_conversation_state(),
        gr.update(choices=[], value=None),
        _conversation_count_text(0),
    )
