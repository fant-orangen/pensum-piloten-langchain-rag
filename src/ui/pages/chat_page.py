"""Embedded RAG chat page for the main Gradio app."""

from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from src.ui.pages.chat_handlers import (
    _MODE_CHOICES,
    _REFERENCE_DEFAULT_STATUS,
    _REFERENCE_HEADERS,
    _bootstrap_chat_on_route_handler,
    _chat_handler,
    _chatbot_select_handler,
    _conversation_count_text,
    _default_conversation_state,
    _empty_reference_rows,
    _load_conversation_handler,
    _new_conversation_handler,
    _open_conversation_text,
    _refresh_handler,
    _reset_scope_handler,
)


@dataclass(slots=True)
class ChatPageComponents:
    """Holds the top-level Gradio components and shared state objects for the chat page."""

    group: gr.Group
    back_button: gr.Button
    token_state: gr.State
    course_id_state: gr.State
    route_state: gr.State


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    """Build the chat Gradio group, wire up all event handlers, and return the page components."""
    with gr.Group(visible=visible) as group:
        token_state = gr.State(None)
        course_id_state = gr.State(None)
        route_state = gr.State(None)
        conversation_state = gr.State(_default_conversation_state())
        source_history_state = gr.State([])

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Samtaler")
                with gr.Group():
                    gr.Markdown("### Ny samtale")
                    mode_selector = gr.Radio(
                        choices=_MODE_CHOICES,
                        value=1,
                        label="Veiledningsmodus",
                        info="Velges for samtalen du starter nå.",
                    )
                    remember_mode_checkbox = gr.Checkbox(
                        value=False,
                        label="Husk som standardmodus for fremtidige samtaler",
                    )
                    new_conversation_button = gr.Button("Start ny samtale", variant="primary")
                refresh_button = gr.Button("Oppdater", variant="secondary")
                conversation_selector = gr.Radio(
                    choices=[],
                    value=None,
                    label=None,
                )
                conversation_count = gr.Markdown(_conversation_count_text(0))

            with gr.Column(scale=4):
                gr.Markdown("# Chat")
                gr.Markdown("Chat med tutor (RAG).")
                open_conversation = gr.Markdown(_open_conversation_text(None))
                status = gr.Markdown("")
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(type="messages", height=700, label="Chat")
                        message = gr.Textbox(
                            label="Melding",
                            placeholder="Spør om pensum ...",
                            lines=2,
                        )

                        with gr.Row():
                            send_button = gr.Button("Send", variant="primary")
                            back_button = gr.Button("Tilbake")
                    with gr.Column(scale=2, min_width=320):
                        gr.Markdown("### Kildereferanser")
                        references_status = gr.Markdown(_REFERENCE_DEFAULT_STATUS)
                        references_table = gr.Dataframe(
                            headers=_REFERENCE_HEADERS,
                            datatype=["str", "str", "str"],
                            value=_empty_reference_rows(),
                            interactive=False,
                            wrap=True,
                            row_count=(0, "dynamic"),
                            col_count=(3, "fixed"),
                        )

    chat_outputs = [
        message,
        chatbot,
        status,
        conversation_state,
        conversation_selector,
        conversation_count,
        open_conversation,
        source_history_state,
        references_table,
        references_status,
    ]
    route_bootstrap_outputs = chat_outputs + [course_id_state]

    send_button.click(
        fn=_chat_handler,
        inputs=[message, chatbot, source_history_state, conversation_state, token_state, course_id_state],
        outputs=chat_outputs,
    )
    message.submit(
        fn=_chat_handler,
        inputs=[message, chatbot, source_history_state, conversation_state, token_state, course_id_state],
        outputs=chat_outputs,
    )
    chatbot.select(
        fn=_chatbot_select_handler,
        inputs=[source_history_state],
        outputs=[references_table, references_status],
    )
    conversation_selector.change(
        fn=_load_conversation_handler,
        inputs=[conversation_selector, token_state, course_id_state],
        outputs=chat_outputs,
    )
    new_conversation_button.click(
        fn=_new_conversation_handler,
        inputs=[token_state, course_id_state, mode_selector, remember_mode_checkbox],
        outputs=chat_outputs,
    )
    refresh_button.click(
        fn=_refresh_handler,
        inputs=[conversation_state, source_history_state, token_state, course_id_state],
        outputs=[
            conversation_selector,
            conversation_count,
            status,
            open_conversation,
            conversation_state,
            source_history_state,
            references_table,
            references_status,
        ],
    )
    route_state.change(
        fn=_bootstrap_chat_on_route_handler,
        inputs=[route_state, token_state, course_id_state],
        outputs=route_bootstrap_outputs,
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

    return ChatPageComponents(
        group=group,
        back_button=back_button,
        token_state=token_state,
        course_id_state=course_id_state,
        route_state=route_state,
    )
