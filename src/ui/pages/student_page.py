"""Student page UI and handlers.

Provides the student landing page where enrolled courses are listed and the
student can navigate to the chat tutor or the A/B comparison view.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.router import ROUTE_AB_COMPARE, ROUTE_CHAT
from src.ui.state import (
    COURSE_ID_KEY,
    ROUTE_KEY,
    auth_token,
    clear_selected_course,
    default_app_state,
    home_route_for_role,
    is_logged_in,
    user_role,
    with_selected_course,
    with_route,
)


@dataclass(slots=True)
class StudentPageComponents:
    """Holds references to every Gradio component on the student landing page."""

    group: gr.Group
    name_text: gr.Markdown
    courses_list: gr.Radio
    status_text: gr.Markdown
    open_ab_button: gr.Button
    open_chat_button: gr.Button
    logout_button: gr.Button


def build_student_page(*, visible: bool) -> StudentPageComponents:
    """Build and return the student landing Gradio group."""
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Student")
        name_text = gr.Markdown("Navn: -")
        gr.Markdown("## Mine fag")
        courses_list = gr.Radio(choices=[], value=None, label="Mine fag")
        status_text = gr.Markdown()
        open_ab_button = gr.Button("Sammenlign RAG vs. ikke-RAG")
        open_chat_button = gr.Button("Chat med tutor")
        logout_button = gr.Button("Logg ut")

    return StudentPageComponents(
        group=group,
        name_text=name_text,
        courses_list=courses_list,
        status_text=status_text,
        open_ab_button=open_ab_button,
        open_chat_button=open_chat_button,
        logout_button=logout_button,
    )


def student_courses_update(state: dict[str, Any]) -> Any:
    """Fetch the student's enrolled courses from the API and return a dropdown update."""
    if not is_logged_in(state) or user_role(state) != "student":
        return gr.update(choices=[], value=None)

    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=None)

    courses, _err = _course_api.list_courses(token)
    choices = [
        (f"{course['name']} ({course['code']})", course["id"])
        for course in courses
        if isinstance(course, dict)
    ]
    selected_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if selected_course_id and any(course_id == selected_course_id for _, course_id in choices):
        return gr.update(choices=choices, value=selected_course_id)
    return gr.update(choices=choices, value=None)


def handle_open_ab_compare(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    """Route the student to the A/B comparison page, clearing any selected course."""
    if not is_logged_in(state):
        return default_app_state(), "", "", ""
    return with_route(clear_selected_course(state), ROUTE_AB_COMPARE), "", "", ""


def handle_open_chat(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    """Route the student to the chat page without a pre-selected course."""
    if not is_logged_in(state):
        return default_app_state(), "", "", ""
    return with_route(clear_selected_course(state), ROUTE_CHAT), "", "", ""


def handle_open_student_course(state: dict[str, Any], course_id: str | None) -> tuple[dict[str, Any], str]:
    """Select the given course and route the student to the chat page for that course."""
    if not is_logged_in(state):
        return default_app_state(), ""
    if not isinstance(course_id, str) or not course_id.strip():
        existing_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
        if state.get(ROUTE_KEY) == ROUTE_CHAT and existing_course_id:
            return state, ""
        return with_route(clear_selected_course(state), home_route_for_role(user_role(state))), ""

    return with_selected_course(
        clear_selected_course(state),
        course_id,
        route=ROUTE_CHAT,
    ), ""


def handle_back_to_student(state: dict[str, Any]) -> tuple[dict[str, Any], str, str, str]:
    """Clear the selected course and route back to the student's home page."""
    if not is_logged_in(state):
        return default_app_state(), "", "", ""
    return with_route(clear_selected_course(state), home_route_for_role(user_role(state))), "", "", ""


def handle_logout() -> tuple[dict[str, Any], str, str, str]:
    """Reset app state to the default unauthenticated state, effectively logging the user out."""
    return default_app_state(), "Du er logget ut.", "", ""
