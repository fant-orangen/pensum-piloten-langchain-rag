"""Embedded RAG chat page component construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.ui.pages.chat_handlers import (
    _MODE_CHOICES,
    _REFERENCE_DEFAULT_STATUS,
    _conversation_count_text,
    _default_conversation_state,
    _empty_reference_panel,
)
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token

CHAT_PAGE_CSS = """
#chat-page {
    padding: 0.5rem 0 1rem;
}

#chat-page-layout {
    gap: 1.25rem;
    align-items: stretch;
}

#chat-sidebar-column,
#chat-main-column {
    min-width: 0;
}

#chat-sidebar-column {
    display: flex;
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
.chat-course-title h1,
.chat-course-title h2,
.chat-course-title h3 {
    margin-bottom: 0;
}

.chat-muted-text p {
    color: #6b7280;
}

.chat-page-toolbar {
    align-items: flex-start;
    gap: 1rem;
    justify-content: space-between;
}

.chat-page-toolbar > div:last-child {
    display: flex;
    justify-content: flex-end;
}

.chat-status-text p {
    margin-bottom: 0;
}

.chat-main-status {
    padding: 0 0.25rem;
}

#chat-sidebar-shell,
.chat-sidebar-panel {
    height: 100%;
    min-height: 0;
}

#chat-sidebar-shell > .gr-block,
#chat-sidebar-shell > div {
    height: 100%;
    min-height: 0;
}

.chat-sidebar-list-section {
    display: flex;
    flex-direction: column;
    flex: 1;
    gap: 0.75rem;
    min-height: 0;
}

#chat-sidebar-list-container {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
    padding-right: 6px;
}

#chat-sidebar-list-container > .gr-block,
#chat-sidebar-list-container > div {
    max-width: 100%;
}

.chat-conversation-summary {
    padding-top: 0.25rem;
    border-top: 1px solid rgba(233, 220, 205, 0.9);
}

#chat-workspace {
    gap: 1rem;
    align-items: stretch;
    flex-wrap: nowrap;
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

#chat-open-references-button,
#chat-close-references-button {
    min-height: 46px;
}

#chat-chat-column,
#chat-references-column {
    min-width: 0;
}

#chat-chat-column {
    flex: 1 1 0 !important;
}

#chat-references-column {
    flex: 0 0 clamp(20rem, 28vw, 28rem) !important;
    max-width: clamp(20rem, 28vw, 28rem);
}

.chat-references-surface {
    height: 100%;
    min-height: 0;
    border: 1px solid #eadac6;
    border-radius: 24px;
    background: linear-gradient(180deg, #fffdfa 0%, #fff6ee 100%);
    box-shadow: 0 18px 40px rgba(107, 76, 34, 0.08);
}

.chat-references-surface > .gr-block,
.chat-references-surface > div {
    height: 100%;
    gap: 0.9rem;
}

.chat-references-header {
    align-items: center;
    gap: 0.75rem;
}

.chat-references-title h3 {
    margin-bottom: 0;
}

#chat-references-panel {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    box-sizing: border-box;
    padding-right: 6px;
}

#chat-references-panel > div {
    max-width: 100%;
}

.chat-reference-panel {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
}

.chat-reference-entry {
    border: 1px solid #eadac6;
    border-radius: 16px;
    background: linear-gradient(180deg, #ffffff 0%, #fffaf4 100%);
    overflow: hidden;
}

.chat-reference-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    cursor: pointer;
    list-style: none;
    font-weight: 600;
}

.chat-reference-summary::-webkit-details-marker {
    display: none;
}

.chat-reference-document {
    min-width: 0;
    word-break: break-word;
}

.chat-reference-page {
    flex-shrink: 0;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    background: #fff0df;
    color: #9a4f00;
    font-size: 0.85rem;
}

.chat-reference-body {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0 1rem 1rem;
    border-top: 1px solid #f1e6da;
}

.chat-reference-meta {
    display: grid;
    gap: 0.35rem;
    padding-top: 0.85rem;
    color: #4b5563;
}

.chat-reference-excerpt {
    padding: 0.9rem 1rem;
    border-radius: 14px;
    background: #fff7ed;
    line-height: 1.5;
    color: #1f2937;
    word-break: break-word;
}

@media (max-width: 1100px) {
    #chat-page-layout {
        flex-wrap: wrap;
    }

    #chat-sidebar-column {
        display: block;
    }

    #chat-workspace {
        flex-wrap: wrap;
    }

    #chat-chat-column,
    #chat-references-column {
        flex: 1 1 100% !important;
        max-width: 100%;
    }

    .chat-references-surface {
        height: auto;
    }

    #chat-sidebar-shell,
    .chat-sidebar-panel {
        height: auto;
    }

    #chat-sidebar-list-container {
        max-height: 20rem;
    }

    #chat-references-panel {
        max-height: 24rem;
    }

    .chat-reference-summary {
        align-items: flex-start;
        flex-direction: column;
    }
}
"""


@dataclass(slots=True)
class ChatPageComponents:
    """Holds all Gradio components and state required by the chat page."""

    group: gr.Group
    sidebar_container: gr.Group
    conversation_list_container: gr.Group
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
    course_title: gr.Markdown
    status: gr.Markdown
    chatbot: gr.Chatbot
    message: gr.Textbox
    send_button: gr.Button
    references_open_state: gr.State
    open_references_button_container: gr.Group
    open_references_button: gr.Button
    close_references_button: gr.Button
    references_container: gr.Column
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
        references_open_state = gr.State(False)

        with gr.Row(elem_id="chat-page-layout"):
            with gr.Column(
                scale=1,
                min_width=280,
                elem_id="chat-sidebar-column",
                elem_classes=["chat-layout-column"],
            ):
                with gr.Group(
                    elem_id="chat-sidebar-shell",
                    elem_classes=["chat-shell-card", "chat-sidebar-panel"],
                ) as sidebar_container:
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
                    with gr.Group(
                        elem_id="chat-sidebar-list-section",
                        elem_classes=["chat-sidebar-list-section"],
                    ):
                        with gr.Group(
                            elem_id="chat-sidebar-list-container",
                            elem_classes=["chat-sidebar-list-container"],
                        ) as conversation_list_container:
                            conversation_selector = gr.Radio(
                                choices=[],
                                value=None,
                                label=None,
                                elem_id="chat-conversation-selector",
                            )
                        conversation_count = gr.Markdown(
                            _conversation_count_text(0),
                            elem_id="chat-conversation-count",
                            elem_classes=["chat-muted-text", "chat-conversation-summary"],
                        )

            with gr.Column(
                scale=4,
                min_width=480,
                elem_id="chat-main-column",
                elem_classes=["chat-layout-column"],
            ):
                with gr.Group(elem_classes=["chat-shell-card", "chat-main-panel"]):
                    with gr.Row(elem_classes=["chat-page-toolbar"]):
                        with gr.Column(scale=4, min_width=320):
                            course_title = gr.Markdown(
                                "## Ingen fag valgt",
                                elem_classes=["chat-course-title"],
                            )
                        with gr.Column(scale=1, min_width=180):
                            with gr.Group(
                                elem_id="chat-open-references-button-container",
                            ) as open_references_button_container:
                                open_references_button = gr.Button(
                                    "Kildereferanser",
                                    variant="secondary",
                                    elem_id="chat-open-references-button",
                                )
                    with gr.Group(elem_classes=["chat-main-status"]):
                        status = gr.Markdown(
                            "",
                            elem_classes=["chat-muted-text", "chat-status-text"],
                        )
                    with gr.Row(elem_id="chat-workspace"):
                        with gr.Column(
                            scale=5,
                            min_width=420,
                            elem_id="chat-chat-column",
                        ):
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
                            visible=False,
                            elem_id="chat-references-column",
                        ) as references_container:
                            with gr.Group(elem_classes=["chat-references-surface"]):
                                with gr.Row(elem_classes=["chat-references-header"]):
                                    gr.Markdown(
                                        "### Kildereferanser",
                                        elem_classes=["chat-references-title"],
                                    )
                                    close_references_button = gr.Button(
                                        "Lukk",
                                        variant="secondary",
                                        elem_id="chat-close-references-button",
                                    )
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
        sidebar_container=sidebar_container,
        conversation_list_container=conversation_list_container,
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
        course_title=course_title,
        status=status,
        chatbot=chatbot,
        message=message,
        send_button=send_button,
        references_open_state=references_open_state,
        open_references_button_container=open_references_button_container,
        open_references_button=open_references_button,
        close_references_button=close_references_button,
        references_container=references_container,
        references_panel=references_panel,
        references_status=references_status,
    )


def _chat_course_title_markdown(course_name: str | None) -> str:
    resolved_name = str(course_name or "").strip() or "Ingen fag valgt"
    return f"## {resolved_name}"


def _chat_course_name_from_scope(token: str | None, course_id: str | None) -> str | None:
    resolved_course_id = str(course_id or "").strip()
    if not token or not resolved_course_id:
        return None

    from src.ui.services.course_service import list_courses

    courses, _err = list_courses(token)
    course = next(
        (
            item
            for item in courses
            if isinstance(item, dict) and str(item.get("id", "")).strip() == resolved_course_id
        ),
        None,
    )
    if course is None:
        return None
    return str(course.get("name", "")).strip() or None


def chat_course_title_from_scope(token: str | None, course_id: str | None) -> str:
    return _chat_course_title_markdown(_chat_course_name_from_scope(token, course_id))


def chat_course_title_text(state: dict[str, Any]) -> str:
    course_name = str(state.get(COURSE_NAME_KEY) or "").strip()
    if course_name:
        return _chat_course_title_markdown(course_name)

    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if not course_id:
        return _chat_course_title_markdown(None)

    return _chat_course_title_markdown(_chat_course_name_from_scope(auth_token(state), course_id))
