"""Embedded RAG chat page component construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.ui.pages.chat_handlers import _conversation_count_text, _default_conversation_state
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token


@dataclass(slots=True)
class ChatPageComponents:
    """Holds all Gradio components and state required by the chat page."""

    group: gr.Group
    sidebar_container: gr.Group
    sidebar_controls_container: gr.Group
    sidebar_conversations_container: gr.Group
    conversation_list_container: gr.Group
    back_button: gr.Button
    token_state: gr.State
    course_id_state: gr.State
    route_state: gr.State
    conversation_state: gr.State
    new_conversation_button: gr.Button
    conversation_selector: gr.Radio
    conversation_count: gr.Markdown
    course_title: gr.Markdown
    status: gr.Markdown
    chatbot: gr.Chatbot
    message: gr.Textbox
    send_button: gr.Button


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    """Build and return the chat page components."""
    with gr.Group(visible=visible, elem_id="chat-page") as group:
        token_state = gr.State(None)
        course_id_state = gr.State(None)
        route_state = gr.State(None)
        conversation_state = gr.State(_default_conversation_state())

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
                    with gr.Group(
                        elem_id="chat-sidebar-controls",
                        elem_classes=["chat-sidebar-controls"],
                    ) as sidebar_controls_container:
                        gr.Markdown("### Ny samtale", elem_classes=["chat-panel-title"])
                        new_conversation_button = gr.Button("Start ny samtale", variant="primary")
                    with gr.Group(
                        elem_id="chat-sidebar-list-section",
                        elem_classes=["chat-sidebar-list-section"],
                        visible=False,
                    ) as sidebar_conversations_container:
                        with gr.Group(
                            elem_id="chat-sidebar-list-container",
                            elem_classes=["chat-sidebar-list-container"],
                        ) as conversation_list_container:
                            conversation_selector = gr.Radio(
                                choices=[],
                                value=None,
                                label=None,
                                show_label=False,
                                elem_id="chat-conversation-selector",
                                visible=False,
                            )
                        conversation_count = gr.Markdown(
                            _conversation_count_text(0),
                            elem_id="chat-conversation-count",
                            elem_classes=["chat-muted-text", "chat-conversation-summary"],
                            visible=False,
                        )

            with gr.Column(
                scale=4,
                min_width=480,
                elem_id="chat-main-column",
                elem_classes=["chat-layout-column"],
            ):
                with gr.Group(elem_classes=["chat-shell-card", "chat-main-panel"]):
                    with gr.Row(elem_classes=["chat-page-toolbar"]):
                        course_title = gr.Markdown(
                            "## Ingen fag valgt",
                            elem_classes=["chat-course-title"],
                        )
                    with gr.Group(elem_classes=["chat-main-status"]):
                        status = gr.Markdown(
                            "",
                            elem_classes=["chat-muted-text", "chat-status-text"],
                        )
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

    return ChatPageComponents(
        group=group,
        sidebar_container=sidebar_container,
        sidebar_controls_container=sidebar_controls_container,
        sidebar_conversations_container=sidebar_conversations_container,
        conversation_list_container=conversation_list_container,
        back_button=back_button,
        token_state=token_state,
        course_id_state=course_id_state,
        route_state=route_state,
        conversation_state=conversation_state,
        new_conversation_button=new_conversation_button,
        conversation_selector=conversation_selector,
        conversation_count=conversation_count,
        course_title=course_title,
        status=status,
        chatbot=chatbot,
        message=message,
        send_button=send_button,
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
