"""Student page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.services import logout_user
from src.ui.router import ROUTE_AB_COMPARE, ROUTE_CHAT, ROUTE_STUDENT
from src.ui.state import default_app_state, is_logged_in, with_route


@dataclass(slots=True)
class StudentPageComponents:
    group: gr.Group
    name_text: gr.Markdown
    status_text: gr.Markdown
    open_ab_button: gr.Button
    open_chat_button: gr.Button
    logout_button: gr.Button


def build_student_page(*, visible: bool) -> StudentPageComponents:
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Student")
        name_text = gr.Markdown("Navn: -")
        status_text = gr.Markdown()
        open_ab_button = gr.Button("Sammenlign RAG vs. ikke-RAG")
        open_chat_button = gr.Button("Chat med tutor")
        logout_button = gr.Button("Logg ut")

    return StudentPageComponents(
        group=group,
        name_text=name_text,
        status_text=status_text,
        open_ab_button=open_ab_button,
        open_chat_button=open_chat_button,
        logout_button=logout_button,
    )


def handle_open_ab_compare(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    if not is_logged_in(state):
        return default_app_state(), "", "", ""
    return with_route(state, ROUTE_AB_COMPARE), "", "", ""


def handle_open_chat(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    if not is_logged_in(state):
        return default_app_state(), "", "", ""
    return with_route(state, ROUTE_CHAT), "", "", ""


def handle_back_to_student(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    if not is_logged_in(state):
        return default_app_state(), "", "", ""
    return with_route(state, ROUTE_STUDENT), "", "", ""


def handle_logout() -> tuple[dict[str, Any], str, str, str]:
    return default_app_state(), logout_user(), "", ""
