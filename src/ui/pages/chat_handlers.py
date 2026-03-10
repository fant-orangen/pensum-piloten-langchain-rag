"""Chat page handlers and helper functions."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.ui.pages.chat_state import (
    ChatConversationState,
    ChatSourceEntry,
    coerce_source_history,
    default_conversation_state,
    empty_reference_rows,
    latest_assistant_sources,
    normalize_conversation_state,
    normalize_source_entry,
    reference_rows_for_sources,
    visible_history_from_source_history,
)
from src.ui.router import ROUTE_CHAT
from src.ui.services.chat_orchestration_service import (
    build_sidebar_model,
    create_chat_conversation,
    fetch_conversations,
    fetch_messages,
    resolve_course_for_chat_entry as resolve_course_for_chat_entry_service,
    selector_choices as selector_choices_service,
    send_chat_message,
)

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


def _empty_reference_rows() -> list[list[str]]:
    return empty_reference_rows()


def _normalize_reference_entry(value: Any) -> ChatSourceEntry | None:
    return normalize_source_entry(value)


def _reference_rows_for_sources(sources: list[dict[str, Any]] | None) -> list[list[str]]:
    return reference_rows_for_sources(sources)


def _visible_history_from_source_history(
    source_history: list[dict[str, Any]] | None,
) -> list[dict[str, str]]:
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in visible_history_from_source_history(source_history)
    ]


def _coerce_source_history(
    visible_history: list[dict[str, Any]],
    source_history: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [
        {"role": msg["role"], "content": msg["content"], "sources": list(msg["sources"])}
        for msg in coerce_source_history(visible_history, source_history)
    ]


def _latest_assistant_sources(
    source_history: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [dict(source) for source in latest_assistant_sources(source_history)]


def _reference_panel_from_sources(sources: list[dict[str, Any]] | None) -> tuple[list[list[str]], str]:
    rows = _reference_rows_for_sources(sources)
    if not rows:
        return _empty_reference_rows(), _REFERENCE_NO_SOURCES_STATUS
    return rows, f"Viser {len(rows)} kildehenvisninger."


def _reference_panel_from_history(
    source_history: list[dict[str, Any]] | None,
) -> tuple[list[list[str]], str]:
    sources = _latest_assistant_sources(source_history)
    if not sources:
        return _empty_reference_rows(), _REFERENCE_DEFAULT_STATUS
    return _reference_panel_from_sources(sources)


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


def _skip_chat_bootstrap_updates() -> tuple[
    str,
    list[dict[str, str]],
    str,
    ChatConversationState,
    Any,
    str,
    str,
    list[dict[str, Any]],
    list[list[str]],
    str,
    str | None,
]:
    skip = gr.skip()
    return (
        skip,
        skip,
        skip,
        skip,
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
) -> tuple[
    str,
    list[dict[str, str]],
    str,
    ChatConversationState,
    Any,
    str,
    str,
    list[dict[str, Any]],
    list[list[str]],
    str,
    str | None,
]:
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
            _open_conversation_text(None),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
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
            _open_conversation_text(None),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
            None,
        )

    status_seed = resolve_status or "Velg eller opprett en samtale først."
    selector_update, count_text, status_text, open_text = _refresh_sidebar(
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
        open_text,
        [],
        _empty_reference_rows(),
        _REFERENCE_DEFAULT_STATUS,
        resolved_course_id,
    )


def _selected_message_index(index: Any) -> int | None:
    if isinstance(index, int):
        return index
    if isinstance(index, (tuple, list)) and index:
        first = index[0]
        if isinstance(first, int):
            return first
    return None


def _chatbot_select_handler(
    source_history: list[dict[str, Any]] | None,
    evt: gr.SelectData,
) -> tuple[list[list[str]], str]:
    if getattr(evt, "selected", True) is False:
        return _reference_panel_from_history(source_history)

    selected_index = _selected_message_index(getattr(evt, "index", None))
    if selected_index is None:
        return _empty_reference_rows(), _REFERENCE_DEFAULT_STATUS

    messages = list(source_history or [])
    if selected_index < 0 or selected_index >= len(messages):
        return _empty_reference_rows(), _REFERENCE_DEFAULT_STATUS

    selected_message = messages[selected_index]
    if selected_message.get("role") != "assistant":
        return _empty_reference_rows(), _REFERENCE_USER_SELECTED_STATUS

    return _reference_panel_from_sources(list(selected_message.get("sources") or []))


def _open_conversation_text(title: str | None) -> str:
    """Format the label shown above the chat area for the currently open conversation."""
    return f"Åpen samtale: {title or 'Ingen'}"


def _conversation_count_text(count: int) -> str:
    """Return a Norwegian summary string for the number of conversations found."""
    if count == 0:
        return "Ingen tidligere samtaler funnet."
    if count == 1:
        return "1 samtale funnet."
    return f"{count} samtaler funnet."


def _selector_choices(conversations: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Convert a list of conversation dicts into (label, id) pairs suitable for a Gradio Radio widget."""
    return selector_choices_service(conversations)


def _fetch_conversations(token: str, course_id: str | None = None) -> tuple[list[dict[str, Any]], str]:
    """Return (conversations, error_message). Conversations are ordered newest-first."""
    return fetch_conversations(token, course_id, no_course_status=_NO_COURSE_STATUS)


def _fetch_messages(token: str, conversation_id: str) -> tuple[list[dict[str, Any]], str]:
    """Return (messages_in_chronological_order, error_message)."""
    return fetch_messages(token, conversation_id)


def _refresh_sidebar(
    token: str,
    selected_id: str | None = None,
    *,
    course_id: str | None = None,
    status_message: str = "",
) -> tuple[Any, str, str, str]:
    """Fetch conversations and return Gradio updates for the sidebar selector, count, status, and open-conversation label."""
    model = build_sidebar_model(
        token,
        course_id=course_id,
        selected_id=selected_id,
        status_message=status_message,
        no_course_status=_NO_COURSE_STATUS,
    )

    return (
        gr.update(choices=model["choices"], value=model["selected_id"]),
        _conversation_count_text(model["count"]),
        model["status_text"],
        _open_conversation_text(model["open_title"]),
    )


def _load_conversation_handler(
    conversation_id: str | None,
    token: str | None,
    course_id: str | None,
) -> tuple[
    str,
    list[dict[str, str]],
    str,
    ChatConversationState,
    Any,
    str,
    str,
    list[dict[str, Any]],
    list[list[str]],
    str,
]:
    """Load message history for the selected conversation and update the chat UI."""
    if not token:
        return (
            "",
            [],
            "Ikke innlogget.",
            _default_conversation_state(),
            gr.update(),
            "",
            _open_conversation_text(None),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id,
            status_message=_NO_COURSE_STATUS,
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    if not conversation_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message="Ingen samtale valgt."
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    conversations, err = _fetch_conversations(token, resolved_course_id)
    if err:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message=err
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    selected_conv = next(
        (c for c in conversations if str(c.get("id", "")) == conversation_id),
        None,
    )
    if selected_conv is None:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id,
            status_message=_OUT_OF_SCOPE_STATUS,
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    source_history, err = _fetch_messages(token, conversation_id)
    if err:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message=err
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    title = selected_conv.get("title") if selected_conv else "Samtale"
    conv_state: ChatConversationState = {
        "conversation_id": conversation_id,
        "title": title,
        "course_id": str(selected_conv.get("course_id", "")) if selected_conv else None,
    }

    selector_update, count_text, status_text, open_text = _refresh_sidebar(
        token,
        conversation_id,
        course_id=course_id,
        status_message=f"Lastet samtale: {title}.",
    )
    reference_rows, reference_status = _reference_panel_from_history(source_history)
    return (
        "",
        _visible_history_from_source_history(source_history),
        status_text,
        conv_state,
        selector_update,
        count_text,
        open_text,
        source_history,
        reference_rows,
        reference_status,
    )


def _new_conversation_handler(
    token: str | None,
    course_id_state: str | None,
    selected_mode: int | None,
    remember_as_default: bool = True,
) -> tuple[
    str,
    list[dict[str, str]],
    str,
    ChatConversationState,
    Any,
    str,
    str,
    list[dict[str, Any]],
    list[list[str]],
    str,
]:
    """Create a new conversation for the resolved course ID and refresh the sidebar."""
    if not token:
        return (
            "",
            [],
            "Ikke innlogget.",
            _default_conversation_state(),
            gr.update(),
            "",
            _open_conversation_text(None),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    course_id = (course_id_state or "").strip()
    if not course_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message=_NO_COURSE_STATUS
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    if selected_mode not in {1, 2, 3}:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id_state,
            status_message="Velg en gyldig veiledningsmodus for ny samtale.",
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    selected_mode = int(selected_mode)
    previous_mode: int | None = None
    previous_mode_message = ""
    temp_mode_set = False

    from src.ui.services.preferences_service import update_system_prompt_mode

    if remember_as_default:
        mode_saved, mode_message = update_system_prompt_mode(token, selected_mode)
        if not mode_saved:
            selector_update, count_text, status_text, open_text = _refresh_sidebar(
                token, course_id=course_id_state, status_message=mode_message
            )
            return (
                "",
                [],
                status_text,
                _default_conversation_state(),
                selector_update,
                count_text,
                open_text,
                [],
                _empty_reference_rows(),
                _REFERENCE_DEFAULT_STATUS,
            )
    else:
        previous_mode, previous_mode_message = _get_user_system_prompt_mode(token)
        if previous_mode is None:
            selector_update, count_text, status_text, open_text = _refresh_sidebar(
                token,
                course_id=course_id_state,
                status_message=previous_mode_message,
            )
            return (
                "",
                [],
                status_text,
                _default_conversation_state(),
                selector_update,
                count_text,
                open_text,
                [],
                _empty_reference_rows(),
                _REFERENCE_DEFAULT_STATUS,
            )
        if previous_mode != selected_mode:
            mode_saved, mode_message = update_system_prompt_mode(token, selected_mode)
            if not mode_saved:
                selector_update, count_text, status_text, open_text = _refresh_sidebar(
                    token, course_id=course_id_state, status_message=mode_message
                )
                return (
                    "",
                    [],
                    status_text,
                    _default_conversation_state(),
                    selector_update,
                    count_text,
                    open_text,
                    [],
                    _empty_reference_rows(),
                    _REFERENCE_DEFAULT_STATUS,
                )
            temp_mode_set = True

    success, message, conv_data = create_chat_conversation(token, course_id)
    if not success or conv_data is None:
        if temp_mode_set and previous_mode is not None:
            restored, restore_message = update_system_prompt_mode(token, previous_mode)
            if not restored:
                message = (
                    f"{message}\n\nKunne ikke gjenopprette standardmodus: {restore_message}"
                )
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message=message
        )
        return (
            "",
            [],
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    conv_id = str(conv_data.get("id", ""))
    title = conv_data.get("title") or "Ny samtale"
    conv_state: ChatConversationState = {
        "conversation_id": conv_id,
        "title": title,
        "course_id": course_id,
    }
    status_message = f"Ny samtale opprettet med {_mode_label(selected_mode)}."
    if remember_as_default:
        status_message = f"{status_message} Denne modusen er nå standard."
    elif temp_mode_set and previous_mode is not None:
        restored, restore_message = update_system_prompt_mode(token, previous_mode)
        if restored:
            status_message = f"{status_message} Standardmodus er uendret."
        else:
            status_message = (
                f"{status_message} Kunne ikke gjenopprette standardmodus: {restore_message}"
            )
    else:
        status_message = f"{status_message} Standardmodus er uendret."

    selector_update, count_text, status_text, open_text = _refresh_sidebar(
        token,
        conv_id,
        course_id=course_id_state,
        status_message=status_message,
    )
    return (
        "",
        [],
        status_text,
        conv_state,
        selector_update,
        count_text,
        open_text,
        [],
        _empty_reference_rows(),
        _REFERENCE_DEFAULT_STATUS,
    )


def _chat_handler(
    user_message: str,
    history: list[dict[str, Any]] | None,
    source_history: list[dict[str, Any]] | None,
    conversation_state: ChatConversationState | dict[str, Any] | None,
    token: str | None,
    course_id_state: str | None,
) -> tuple[
    str,
    list[dict[str, str]],
    str,
    ChatConversationState,
    Any,
    str,
    str,
    list[dict[str, Any]],
    list[list[str]],
    str,
]:
    """Send the user message to the backend and append both the user and AI turns to the chat history."""
    visible_history = [
        {"role": str(msg.get("role", "")), "content": str(msg.get("content", ""))}
        for msg in (history or [])
        if isinstance(msg, dict) and msg.get("role") in {"user", "assistant"}
    ]
    resolved_source_history = _coerce_source_history(visible_history, source_history)
    reference_rows, reference_status = _reference_panel_from_history(resolved_source_history)
    text = (user_message or "").strip()
    current_state = normalize_conversation_state(conversation_state)

    if not token:
        return (
            "",
            visible_history,
            "Ikke innlogget.",
            current_state,
            gr.update(),
            "",
            _open_conversation_text(None),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    if not (course_id_state or "").strip():
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id_state,
            status_message=_NO_COURSE_STATUS,
        )
        return (
            "",
            visible_history,
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    active_course_id = str(course_id_state or "").strip()
    if not text:
        conv_id = current_state.get("conversation_id")
        selector_update, count_text, status_text, open_text = _refresh_sidebar(token, conv_id, course_id=course_id_state)
        return (
            "",
            visible_history,
            status_text,
            current_state,
            selector_update,
            count_text,
            open_text,
            resolved_source_history,
            reference_rows,
            reference_status,
        )

    conv_id = current_state.get("conversation_id")
    conv_course_id = str(current_state.get("course_id") or "").strip()
    if conv_id and conv_course_id != active_course_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id_state,
            status_message=_OUT_OF_SCOPE_STATUS,
        )
        return (
            "",
            visible_history,
            status_text,
            _default_conversation_state(),
            selector_update,
            count_text,
            open_text,
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )
    if not conv_id:
        # Auto-create the first conversation so the user's first send is actionable.
        created, created_message, conv_data = create_chat_conversation(token, active_course_id)
        if not created or conv_data is None:
            selector_update, count_text, status_text, open_text = _refresh_sidebar(
                token,
                course_id=course_id_state,
                status_message=created_message,
            )
            return (
                "",
                visible_history,
                status_text,
                current_state,
                selector_update,
                count_text,
                open_text,
                resolved_source_history,
                reference_rows,
                reference_status,
            )
        conv_id = str(conv_data.get("id", "")).strip()
        if not conv_id:
            selector_update, count_text, status_text, open_text = _refresh_sidebar(
                token,
                course_id=course_id_state,
                status_message="Kunne ikke opprette ny samtale.",
            )
            return (
                "",
                visible_history,
                status_text,
                current_state,
                selector_update,
                count_text,
                open_text,
                resolved_source_history,
                reference_rows,
                reference_status,
            )
        current_state = {
            "conversation_id": conv_id,
            "title": conv_data.get("title") or "Ny samtale",
            "course_id": active_course_id,
        }

    success, err, ai_msg_data = send_chat_message(token, conv_id, text)
    if not success or ai_msg_data is None:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(token, conv_id, course_id=course_id_state, status_message=err)
        return (
            "",
            visible_history,
            status_text,
            current_state,
            selector_update,
            count_text,
            open_text,
            resolved_source_history,
            reference_rows,
            reference_status,
        )

    ai_content = ai_msg_data.get("content", "")
    updated_source_history = resolved_source_history + [
        {"role": "user", "content": text, "sources": []},
        {
            "role": "assistant",
            "content": ai_content,
            "sources": list(ai_msg_data.get("sources") or []),
        },
    ]
    updated_history = _visible_history_from_source_history(updated_source_history)
    updated_reference_rows, updated_reference_status = _reference_panel_from_history(
        updated_source_history
    )

    selector_update, count_text, status_text, open_text = _refresh_sidebar(token, conv_id, course_id=course_id_state)
    return (
        "",
        updated_history,
        status_text,
        current_state,
        selector_update,
        count_text,
        open_text,
        updated_source_history,
        updated_reference_rows,
        updated_reference_status,
    )


def _refresh_handler(
    conversation_state: ChatConversationState | dict[str, Any] | None,
    source_history: list[dict[str, Any]] | None,
    token: str | None,
    course_id_state: str | None,
) -> tuple[Any, str, str, str, ChatConversationState, list[dict[str, Any]], list[list[str]], str]:
    """Re-fetch the conversation list and return updated sidebar components."""
    current_state = normalize_conversation_state(conversation_state)

    if not token:
        return (
            gr.update(choices=[], value=None),
            "",
            "Ikke innlogget.",
            _open_conversation_text(None),
            _default_conversation_state(),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    if not (course_id_state or "").strip():
        return (
            gr.update(choices=[], value=None),
            _conversation_count_text(0),
            _NO_COURSE_STATUS,
            _open_conversation_text(None),
            _default_conversation_state(),
            [],
            _empty_reference_rows(),
            _REFERENCE_DEFAULT_STATUS,
        )

    active_course_id = str(course_id_state or "").strip()
    conv_id = str(current_state.get("conversation_id") or "").strip()
    conversations, err = _fetch_conversations(token, active_course_id)
    choices = _selector_choices(conversations)
    resolved_value = conv_id if conv_id and any(item[1] == conv_id for item in choices) else None
    selected_conv = next(
        (item for item in conversations if str(item.get("id", "")) == resolved_value),
        None,
    )
    next_state: ChatConversationState = {
        "conversation_id": resolved_value,
        "title": selected_conv.get("title") if selected_conv else None,
        "course_id": active_course_id if selected_conv else None,
    }
    next_source_history = list(source_history or []) if resolved_value else []
    reference_rows, reference_status = _reference_panel_from_history(next_source_history)
    status_text = err or "Samtalelisten er oppdatert."
    return (
        gr.update(choices=choices, value=resolved_value),
        _conversation_count_text(len(conversations)),
        status_text,
        _open_conversation_text(next_state.get("title")),
        next_state if resolved_value else _default_conversation_state(),
        next_source_history,
        reference_rows if resolved_value else _empty_reference_rows(),
        reference_status if resolved_value else _REFERENCE_DEFAULT_STATUS,
    )


def _reset_scope_handler(
    token: str | None,
    course_id_state: str | None,
) -> tuple[
    str,
    list[dict[str, str]],
    str,
    ChatConversationState,
    Any,
    str,
    str,
    list[dict[str, Any]],
    list[list[str]],
    str,
]:
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
        _open_conversation_text(None),
        [],
        _empty_reference_rows(),
        _REFERENCE_DEFAULT_STATUS,
    )
