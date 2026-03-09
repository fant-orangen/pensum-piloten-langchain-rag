"""Embedded RAG chat page for the main Gradio app.

Renders a conversation sidebar and a chat interface backed by the FastAPI
conversation service. A valid JWT token must be present in token_state for the
page to function. Conversations and messages are persisted through the backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import shorten
from typing import Any

import gradio as gr

_TITLE_WIDTH = 56
_MODE_CHOICES = [
    ("Socratic mode", 1),
    ("Direct mode", 2),
    ("Example mode", 3),
]
_NO_COURSE_STATUS = "Velg et fag før du bruker chat."


@dataclass(slots=True)
class ChatPageComponents:
    """Holds the top-level Gradio components and shared state objects for the chat page."""

    group: gr.Group
    back_button: gr.Button
    token_state: gr.State
    course_id_state: gr.State


def _default_conversation_state() -> dict[str, Any]:
    """Return an empty conversation state dict with all fields set to None."""
    return {"conversation_id": None, "title": None, "course_id": None}


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
    choices = []
    for conv in conversations:
        title = conv.get("title") or "Samtale"
        updated_at = conv.get("updated_at", "")
        label = shorten(f"{title} — {updated_at[:16]}", width=60, placeholder="…")
        choices.append((label, str(conv.get("id", ""))))
    return choices


def _fetch_conversations(token: str, course_id: str | None = None) -> tuple[list[dict[str, Any]], str]:
    """Return (conversations, error_message). Conversations are ordered newest-first."""
    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        return [], _NO_COURSE_STATUS

    from src.ui.services.conversation_service import list_conversations
    items, _total, err = list_conversations(token, course_id=resolved_course_id)
    return items, err


def _fetch_messages(token: str, conversation_id: str) -> tuple[list[dict[str, str]], str]:
    """Return (messages_in_chronological_order, error_message)."""
    from src.ui.services.conversation_service import get_messages

    all_messages: list[dict[str, str]] = []
    page = 1
    while True:
        items, total, err = get_messages(token, conversation_id, page=page, page_size=50)
        if err:
            return [], err
        all_messages.extend(items)
        if len(all_messages) >= total or not items:
            break
        page += 1

    # API returns newest-first; reverse to chronological order.
    all_messages.reverse()
    history = []
    for msg in all_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "human":
            history.append({"role": "user", "content": content})
        elif role == "ai":
            history.append({"role": "assistant", "content": content})
    return history, ""


def _refresh_sidebar(
    token: str,
    selected_id: str | None = None,
    *,
    course_id: str | None = None,
    status_message: str = "",
) -> tuple[Any, str, str, str]:
    """Fetch conversations and return Gradio updates for the sidebar selector, count, status, and open-conversation label."""
    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        status_text = status_message or _NO_COURSE_STATUS
        return (
            gr.update(choices=[], value=None),
            _conversation_count_text(0),
            status_text,
            _open_conversation_text(None),
        )

    conversations, err = _fetch_conversations(token, resolved_course_id)
    if err:
        status_message = err

    choices = _selector_choices(conversations)
    resolved_value = selected_id if any(v == selected_id for _, v in choices) else None

    selected_conv = next(
        (c for c in conversations if str(c.get("id", "")) == resolved_value),
        None,
    )
    title = selected_conv.get("title") if selected_conv else None

    return (
        gr.update(choices=choices, value=resolved_value),
        _conversation_count_text(len(conversations)),
        status_message,
        _open_conversation_text(title),
    )


def _save_mode_handler(selected_mode: int | None, token: str | None, current_status: str) -> str:
    """Persist the selected tutoring mode for the authenticated user."""
    if not token:
        return "Ikke innlogget."
    if selected_mode not in {1, 2, 3}:
        return "Velg en gyldig veiledningsmodus."

    from src.ui.services.preferences_service import update_system_prompt_mode

    success, message = update_system_prompt_mode(token, int(selected_mode))
    if success:
        return f"{message} New conversations will use this mode."
    if current_status:
        return f"{current_status}\n\n{message}"
    return message


def _load_conversation_handler(
    conversation_id: str | None,
    token: str | None,
    course_id: str | None,
) -> tuple[str, list[dict[str, str]], str, dict[str, Any], Any, str, str]:
    """Load message history for the selected conversation and update the chat UI."""
    if not token:
        return "", [], "Ikke innlogget.", _default_conversation_state(), gr.update(), "", _open_conversation_text(None)

    resolved_course_id = (course_id or "").strip()
    if not resolved_course_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id,
            status_message=_NO_COURSE_STATUS,
        )
        return "", [], status_text, _default_conversation_state(), selector_update, count_text, open_text

    if not conversation_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message="Ingen samtale valgt."
        )
        return "", [], status_text, _default_conversation_state(), selector_update, count_text, open_text

    history, err = _fetch_messages(token, conversation_id)
    if err:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id, status_message=err
        )
        return "", [], status_text, _default_conversation_state(), selector_update, count_text, open_text

    conversations, _ = _fetch_conversations(token, course_id)
    selected_conv = next(
        (c for c in conversations if str(c.get("id", "")) == conversation_id),
        None,
    )
    title = selected_conv.get("title") if selected_conv else "Samtale"
    conv_state = {
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
    return "", history, status_text, conv_state, selector_update, count_text, open_text


def _new_conversation_handler(
    token: str | None,
    course_id_input: str,
    course_id_state: str | None,
    selected_mode: int | None,
) -> tuple[str, list[dict[str, str]], str, dict[str, Any], Any, str, str]:
    """Create a new conversation for the resolved course ID and refresh the sidebar."""
    if not token:
        return "", [], "Ikke innlogget.", _default_conversation_state(), gr.update(), "", _open_conversation_text(None)

    course_id = (course_id_state or "").strip()
    if not course_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message=_NO_COURSE_STATUS
        )
        return "", [], status_text, _default_conversation_state(), selector_update, count_text, open_text

    if selected_mode in {1, 2, 3}:
        from src.ui.services.preferences_service import update_system_prompt_mode

        mode_saved, mode_message = update_system_prompt_mode(token, int(selected_mode))
        if not mode_saved:
            selector_update, count_text, status_text, open_text = _refresh_sidebar(
                token, course_id=course_id_state, status_message=mode_message
            )
            return "", [], status_text, _default_conversation_state(), selector_update, count_text, open_text

    from src.ui.services.conversation_service import create_conversation
    success, message, conv_data = create_conversation(token, course_id)
    if not success or conv_data is None:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message=message
        )
        return "", [], status_text, _default_conversation_state(), selector_update, count_text, open_text

    conv_id = str(conv_data.get("id", ""))
    title = conv_data.get("title") or "Ny samtale"
    conv_state = {
        "conversation_id": conv_id,
        "title": title,
        "course_id": course_id,
    }
    selector_update, count_text, status_text, open_text = _refresh_sidebar(
        token,
        conv_id,
        course_id=course_id_state,
        status_message="Ny samtale opprettet med valgt veiledningsmodus.",
    )
    return "", [], status_text, conv_state, selector_update, count_text, open_text


def _chat_handler(
    user_message: str,
    history: list[dict[str, Any]] | None,
    conversation_state: dict[str, Any] | None,
    token: str | None,
    course_id_state: str | None,
) -> tuple[str, list[dict[str, str]], str, dict[str, Any], Any, str, str]:
    """Send the user message to the backend and append both the user and AI turns to the chat history."""
    visible_history = [
        msg
        for msg in (history or [])
        if isinstance(msg, dict) and msg.get("role") in {"user", "assistant"}
    ]
    text = (user_message or "").strip()

    if not token:
        return "", visible_history, "Ikke innlogget.", conversation_state or _default_conversation_state(), gr.update(), "", _open_conversation_text(None)

    if not (course_id_state or "").strip():
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token,
            course_id=course_id_state,
            status_message=_NO_COURSE_STATUS,
        )
        return "", visible_history, status_text, _default_conversation_state(), selector_update, count_text, open_text

    if not text:
        conv_id = (conversation_state or {}).get("conversation_id")
        selector_update, count_text, status_text, open_text = _refresh_sidebar(token, conv_id, course_id=course_id_state)
        return "", visible_history, status_text, conversation_state or _default_conversation_state(), selector_update, count_text, open_text

    conv_id = (conversation_state or {}).get("conversation_id")
    if not conv_id:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(
            token, course_id=course_id_state, status_message="Velg eller opprett en samtale først."
        )
        return "", visible_history, status_text, conversation_state or _default_conversation_state(), selector_update, count_text, open_text

    from src.ui.services.conversation_service import send_message
    success, err, ai_msg_data = send_message(token, conv_id, text)
    if not success or ai_msg_data is None:
        selector_update, count_text, status_text, open_text = _refresh_sidebar(token, conv_id, course_id=course_id_state, status_message=err)
        return "", visible_history, status_text, conversation_state or _default_conversation_state(), selector_update, count_text, open_text

    ai_content = ai_msg_data.get("content", "")
    updated_history = visible_history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": ai_content},
    ]

    selector_update, count_text, status_text, open_text = _refresh_sidebar(token, conv_id, course_id=course_id_state)
    return "", updated_history, status_text, conversation_state or _default_conversation_state(), selector_update, count_text, open_text


def _refresh_handler(
    conversation_state: dict[str, Any] | None,
    token: str | None,
    course_id_state: str | None,
) -> tuple[Any, str, str, str, dict[str, Any]]:
    """Re-fetch the conversation list and return updated sidebar components."""
    if not token:
        return gr.update(choices=[], value=None), "", "Ikke innlogget.", _open_conversation_text(None), _default_conversation_state()

    if not (course_id_state or "").strip():
        return (
            gr.update(choices=[], value=None),
            _conversation_count_text(0),
            _NO_COURSE_STATUS,
            _open_conversation_text(None),
            _default_conversation_state(),
        )

    conv_id = (conversation_state or {}).get("conversation_id")
    selector_update, count_text, status_text, open_text = _refresh_sidebar(
        token, conv_id, course_id=course_id_state, status_message="Samtalelisten er oppdatert."
    )
    return selector_update, count_text, status_text, open_text, conversation_state or _default_conversation_state()


def _reset_scope_handler(
    token: str | None,
    course_id_state: str | None,
) -> tuple[str, list[dict[str, str]], str, dict[str, Any], Any, str, str]:
    """Reset local chat state when auth/course scope changes."""
    del token
    del course_id_state
    return (
        "",
        [],
        "",
        _default_conversation_state(),
        gr.update(choices=[], value=None),
        _conversation_count_text(0),
        _open_conversation_text(None),
    )


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    """Build the chat Gradio group, wire up all event handlers, and return the page components."""
    with gr.Group(visible=visible) as group:
        token_state = gr.State(None)
        course_id_state = gr.State(None)
        conversation_state = gr.State(_default_conversation_state())

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Samtaler")
                course_id_input = gr.Textbox(
                    label="Fag-ID",
                    placeholder="Lim inn fag-ID for å starte ny samtale",
                    visible=False,
                )
                with gr.Row():
                    new_conversation_button = gr.Button("Ny samtale", variant="secondary")
                    refresh_button = gr.Button("Oppdater")
                conversation_selector = gr.Radio(
                    choices=[],
                    value=None,
                    label=None,
                )
                conversation_count = gr.Markdown(_conversation_count_text(0))

            with gr.Column(scale=4):
                with gr.Row():
                    gr.Markdown("# Chat")
                    with gr.Column(scale=1, min_width=280):
                        mode_selector = gr.Radio(
                            choices=_MODE_CHOICES,
                            value=1,
                            label="Tutoring mode",
                            info="Choose the mode for new conversations.",
                        )
                        save_mode_button = gr.Button("Save mode", variant="secondary")
                gr.Markdown("Chat med tutor (RAG).")
                open_conversation = gr.Markdown(_open_conversation_text(None))
                status = gr.Markdown("")
                chatbot = gr.Chatbot(type="messages", height=700, label="Chat")
                message = gr.Textbox(
                    label="Melding",
                    placeholder="Spør om pensum ...",
                    lines=2,
                )

                with gr.Row():
                    send_button = gr.Button("Send", variant="primary")
                    back_button = gr.Button("Tilbake")

    chat_outputs = [
        message,
        chatbot,
        status,
        conversation_state,
        conversation_selector,
        conversation_count,
        open_conversation,
    ]

    send_button.click(
        fn=_chat_handler,
        inputs=[message, chatbot, conversation_state, token_state, course_id_state],
        outputs=chat_outputs,
    )
    message.submit(
        fn=_chat_handler,
        inputs=[message, chatbot, conversation_state, token_state, course_id_state],
        outputs=chat_outputs,
    )
    conversation_selector.change(
        fn=_load_conversation_handler,
        inputs=[conversation_selector, token_state, course_id_state],
        outputs=chat_outputs,
    )
    new_conversation_button.click(
        fn=_new_conversation_handler,
        inputs=[token_state, course_id_input, course_id_state, mode_selector],
        outputs=chat_outputs,
    )
    mode_selector.change(
        fn=_save_mode_handler,
        inputs=[mode_selector, token_state, status],
        outputs=[status],
    )
    refresh_button.click(
        fn=_refresh_handler,
        inputs=[conversation_state, token_state, course_id_state],
        outputs=[
            conversation_selector,
            conversation_count,
            status,
            open_conversation,
            conversation_state,
        ],
    )
    save_mode_button.click(
        fn=_save_mode_handler,
        inputs=[mode_selector, token_state, status],
        outputs=[status],
    )
    token_state.change(
        fn=_reset_scope_handler,
        inputs=[token_state, course_id_state],
        outputs=chat_outputs,
    )
    course_id_state.change(
        fn=_reset_scope_handler,
        inputs=[token_state, course_id_state],
        outputs=chat_outputs,
    )

    return ChatPageComponents(group=group, back_button=back_button, token_state=token_state, course_id_state=course_id_state)
