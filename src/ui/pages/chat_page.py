"""Embedded RAG chat page component construction."""

from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from src.ui.pages.chat_handlers import (
    _MODE_CHOICES,
    _REFERENCE_DEFAULT_STATUS,
    _REFERENCE_HEADERS,
    _conversation_count_text,
    _default_conversation_state,
    _empty_reference_rows,
    _open_conversation_text,
)


@dataclass(slots=True)
class ChatPageComponents:
    """Holds all Gradio components and state required by the chat page."""

    group: gr.Group
    back_button: gr.Button
    token_state: gr.State
    course_id_state: gr.State
    route_state: gr.State
    conversation_state: gr.State
    source_history_state: gr.State
    mode_selector: gr.Radio
    new_conversation_button: gr.Button
    refresh_button: gr.Button
    conversation_selector: gr.Radio
    conversation_count: gr.Markdown
    open_conversation: gr.Markdown
    status: gr.Markdown
    chatbot: gr.Chatbot
    message: gr.Textbox
    send_button: gr.Button
    references_table: gr.Dataframe
    references_status: gr.Markdown


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    """Build and return the chat page components."""
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
                        info="Brukes for nye samtaler og blir standard til du endrer den.",
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

    return ChatPageComponents(
        group=group,
        back_button=back_button,
        token_state=token_state,
        course_id_state=course_id_state,
        route_state=route_state,
        conversation_state=conversation_state,
        source_history_state=source_history_state,
        mode_selector=mode_selector,
        new_conversation_button=new_conversation_button,
        refresh_button=refresh_button,
        conversation_selector=conversation_selector,
        conversation_count=conversation_count,
        open_conversation=open_conversation,
        status=status,
        chatbot=chatbot,
        message=message,
        send_button=send_button,
        references_table=references_table,
        references_status=references_status,
    )
