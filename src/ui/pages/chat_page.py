"""Embedded RAG chat page component construction."""

from __future__ import annotations

from dataclasses import dataclass

import gradio as gr

from src.ui.pages.chat_handlers import (
    _MODE_CHOICES,
    _REFERENCE_DEFAULT_STATUS,
    _conversation_count_text,
    _default_conversation_state,
    _empty_reference_panel,
    _open_conversation_text,
)

CHAT_PAGE_CSS = """
#chat-page {
    padding: 0.5rem 0 1rem;
}

#chat-page-layout {
    gap: 1.25rem;
    align-items: stretch;
}

#chat-sidebar-column,
#chat-main-column,
#chat-references-column {
    min-width: 0;
}

.chat-shell-card {
    border: 1px solid #e9dccd;
    border-radius: 20px;
    background: linear-gradient(180deg, #fffdfa 0%, #fff6ee 100%);
    box-shadow: 0 18px 40px rgba(107, 76, 34, 0.08);
}

.chat-shell-card > .gr-block,
.chat-shell-card > div {
    gap: 0.9rem;
}

.chat-panel-title h2,
.chat-panel-title h3,
.chat-page-title h1 {
    margin-bottom: 0;
}

.chat-page-subtitle p,
.chat-muted-text p {
    color: #6b7280;
}

.chat-status-text p {
    margin-bottom: 0;
}

.chat-conversation-summary {
    padding-top: 0.25rem;
    border-top: 1px solid rgba(233, 220, 205, 0.9);
}

#chat-workspace {
    gap: 1rem;
    align-items: stretch;
}

.chat-workspace-panel {
    height: 100%;
}

.chat-workspace-panel > .gr-block,
.chat-workspace-panel > div {
    gap: 0.9rem;
}

#chat-main-actions {
    gap: 0.75rem;
}

#chat-main-actions > button {
    min-height: 48px;
}

#chat-main-actions > button:first-child {
    flex: 1.2;
}

#chat-main-actions > button:last-child {
    flex: 0.8;
}

#chat-message-composer textarea {
    min-height: 96px;
}

#chat-message-composer {
    border-radius: 16px;
}

#chat-references-panel {
    max-height: 700px;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
    padding-right: 6px;
}

#chat-references-panel > div {
    max-width: 100%;
}

#chat-references-accordion {
    border: 1px solid #eadac6;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.72);
}

#chat-references-accordion label,
#chat-references-accordion summary {
    font-weight: 700;
}

@media (max-width: 1100px) {
    #chat-page-layout {
        flex-wrap: wrap;
    }

    #chat-workspace {
        flex-wrap: wrap;
    }
}
"""


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
    references_accordion: gr.Accordion
    references_panel: gr.HTML
    references_status: gr.Markdown


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    """Build and return the chat page components."""
    with gr.Group(visible=visible, elem_id="chat-page") as group:
        token_state = gr.State(None)
        course_id_state = gr.State(None)
        route_state = gr.State(None)
        conversation_state = gr.State(_default_conversation_state())
        source_history_state = gr.State([])

        with gr.Row(elem_id="chat-page-layout"):
            with gr.Column(
                scale=1,
                min_width=280,
                elem_id="chat-sidebar-column",
                elem_classes=["chat-layout-column"],
            ):
                with gr.Group(elem_classes=["chat-shell-card", "chat-sidebar-panel"]):
                    gr.Markdown("## Samtaler", elem_classes=["chat-panel-title"])
                    with gr.Group():
                        gr.Markdown("### Ny samtale", elem_classes=["chat-panel-title"])
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
                    conversation_count = gr.Markdown(
                        _conversation_count_text(0),
                        elem_classes=["chat-muted-text", "chat-conversation-summary"],
                    )

            with gr.Column(
                scale=4,
                min_width=480,
                elem_id="chat-main-column",
                elem_classes=["chat-layout-column"],
            ):
                with gr.Group(elem_classes=["chat-shell-card", "chat-main-panel"]):
                    gr.Markdown("# Chat", elem_classes=["chat-page-title"])
                    gr.Markdown("Chat med tutor (RAG).", elem_classes=["chat-page-subtitle"])
                    open_conversation = gr.Markdown(
                        _open_conversation_text(None),
                        elem_classes=["chat-status-text"],
                    )
                    status = gr.Markdown("", elem_classes=["chat-muted-text", "chat-status-text"])
                    with gr.Row(elem_id="chat-workspace"):
                        with gr.Column(scale=4, min_width=420):
                            with gr.Group(
                                elem_classes=["chat-shell-card", "chat-workspace-panel"],
                            ):
                                chatbot = gr.Chatbot(type="messages", height=700, label="Chat")
                                message = gr.Textbox(
                                    label="Melding",
                                    placeholder="Spør om pensum ...",
                                    lines=2,
                                    elem_id="chat-message-composer",
                                )

                                with gr.Row(elem_id="chat-main-actions"):
                                    send_button = gr.Button("Send", variant="primary")
                                    back_button = gr.Button("Tilbake")

                        with gr.Column(
                            scale=2,
                            min_width=320,
                            elem_id="chat-references-column",
                            elem_classes=["chat-layout-column"],
                        ):
                            with gr.Group(
                                elem_classes=["chat-shell-card", "chat-workspace-panel"],
                            ):
                                references_accordion = gr.Accordion(
                                    "Kildereferanser",
                                    open=True,
                                    elem_id="chat-references-accordion",
                                )
                                with references_accordion:
                                    references_status = gr.Markdown(
                                        _REFERENCE_DEFAULT_STATUS,
                                        elem_classes=["chat-muted-text", "chat-status-text"],
                                    )
                                    references_panel = gr.HTML(
                                        value=_empty_reference_panel(),
                                        elem_id="chat-references-panel",
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
        references_accordion=references_accordion,
        references_panel=references_panel,
        references_status=references_status,
    )
