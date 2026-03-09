"""Teacher page UI and handlers.

Provides the teacher landing page where a teacher can view courses they are
responsible for, browse available courses, create new courses, and navigate
into the course detail view.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.router import ROUTE_CHAT, ROUTE_TEACHER_COURSE
from src.ui.state import (
    COURSE_ID_KEY,
    NAME_KEY,
    ROUTE_KEY,
    auth_token,
    clear_selected_course,
    is_logged_in,
    user_role,
    with_selected_course,
)


@dataclass(slots=True)
class TeacherPageComponents:
    """Holds references to every Gradio component on the teacher landing page."""

    group: gr.Group
    name_text: gr.Markdown
    responsible_list: gr.Radio
    available_list: gr.Radio
    add_course_name: gr.Textbox
    add_course_button: gr.Button
    status_text: gr.Markdown
    logout_button: gr.Button


def teacher_name_text(state: dict[str, Any]) -> str:
    """Return a formatted name string for display on the teacher page."""
    name = str(state.get(NAME_KEY) or "").strip()
    return f"Navn: {name or '-'}"


def _course_choices(courses: list[Any]) -> list[tuple[str, str]]:
    """Convert a list of course dicts into (label, id) pairs for a Gradio Radio widget."""
    return [
        (f"{course['name']} ({course['code']})", course["id"])
        for course in courses
        if isinstance(course, dict)
    ]


def teacher_responsible_courses_update(state: dict[str, Any]) -> Any:
    """Fetch courses the teacher is responsible for and return a Radio update, preserving any previously selected course."""
    if not is_logged_in(state) or user_role(state) != "teacher":
        return gr.update(choices=[], value=None)

    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=None)

    courses, _err = _course_api.list_responsible_courses(token)
    choices = _course_choices(courses)
    selected_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if selected_course_id and any(course_id == selected_course_id for _, course_id in choices):
        return gr.update(choices=choices, value=selected_course_id)
    return gr.update(choices=choices, value=None)


def teacher_available_courses_update(state: dict[str, Any]) -> Any:
    """Fetch student-only courses for the teacher and return a Radio update."""
    if not is_logged_in(state) or user_role(state) != "teacher":
        return gr.update(choices=[], value=None)

    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=None)

    available_courses, _err = _course_api.list_available_courses(token)
    responsible_courses, _err = _course_api.list_responsible_courses(token)
    responsible_ids = {
        str(course.get("id"))
        for course in responsible_courses
        if isinstance(course, dict) and course.get("id")
    }
    student_only_courses = [
        course
        for course in available_courses
        if isinstance(course, dict) and str(course.get("id")) not in responsible_ids
    ]
    choices = _course_choices(student_only_courses)
    selected_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if selected_course_id and any(course_id == selected_course_id for _, course_id in choices):
        return gr.update(choices=choices, value=selected_course_id)
    return gr.update(choices=choices, value=None)


def build_teacher_page(*, visible: bool) -> TeacherPageComponents:
    """Build and return the teacher landing Gradio group."""
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Lærer")
        name_text = gr.Markdown("Navn: -")
        gr.Markdown("## Ansvarlig for")
        responsible_list = gr.Radio(choices=[], value=None, label="Ansvarlig for")
        gr.Markdown("## Tilgjengelige fag")
        available_list = gr.Radio(choices=[], value=None, label="Tilgjengelige fag")
        gr.Markdown("## Legg til fag")
        add_course_name = gr.Textbox(label="Nytt fag")
        add_course_button = gr.Button("Legg til fag", variant="primary")
        status_text = gr.Markdown()
        logout_button = gr.Button("Logg ut")

    return TeacherPageComponents(
        group=group,
        name_text=name_text,
        responsible_list=responsible_list,
        available_list=available_list,
        add_course_name=add_course_name,
        add_course_button=add_course_button,
        status_text=status_text,
        logout_button=logout_button,
    )


def handle_add_course(state: dict[str, Any], course_name: str) -> tuple[str, Any, Any, str]:
    """Create a new course from the given name and refresh both teacher lists."""
    if not is_logged_in(state) or user_role(state) != "teacher":
        return (
            course_name,
            teacher_responsible_courses_update(state),
            teacher_available_courses_update(state),
            "Ikke tillatt.",
        )

    token = auth_token(state)
    if not token:
        return (
            course_name,
            teacher_responsible_courses_update(state),
            teacher_available_courses_update(state),
            "Sessionen er utløpt — logg inn på nytt.",
        )

    cleaned_name = course_name.strip()
    if not cleaned_name:
        return (
            course_name,
            teacher_responsible_courses_update(state),
            teacher_available_courses_update(state),
            "Fyll ut fagnavnet.",
        )

    # Derive a course code from the name (uppercase, spaces → underscores, max 20 chars).
    code = cleaned_name.upper().replace(" ", "_")[:20]
    # Use the code as the chroma collection name and a default documents directory.
    chroma_collection = code.lower()
    documents_dir = f"data/documents/{chroma_collection}"

    success, message, _ = _course_api.create_course(
        token, cleaned_name, code, chroma_collection, documents_dir
    )
    next_input_value = "" if success else course_name
    return (
        next_input_value,
        teacher_responsible_courses_update(state),
        teacher_available_courses_update(state),
        message,
    )


def handle_open_teacher_course(state: dict[str, Any], course_id: str | None) -> tuple[dict[str, Any], str]:
    """Validate the selected student-only course and route the teacher to chat."""
    if not is_logged_in(state) or user_role(state) != "teacher":
        return clear_selected_course(state), "Ikke tillatt."
    if not isinstance(course_id, str) or not course_id.strip():
        existing_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
        if state.get(ROUTE_KEY) == ROUTE_TEACHER_COURSE and existing_course_id:
            return state, ""
        return clear_selected_course(state), ""

    token = auth_token(state)
    if not token:
        return clear_selected_course(state), "Sessionen er utløpt — logg inn på nytt."

    available_courses, _err = _course_api.list_available_courses(token)
    responsible_courses, _err = _course_api.list_responsible_courses(token)
    responsible_ids = {
        str(item.get("id"))
        for item in responsible_courses
        if isinstance(item, dict) and item.get("id")
    }
    courses = [
        course
        for course in available_courses
        if isinstance(course, dict) and str(course.get("id")) not in responsible_ids
    ]
    course = next(
        (c for c in courses if isinstance(c, dict) and c.get("id") == course_id),
        None,
    )
    if course is None:
        return clear_selected_course(state), "Fant ikke faget."

    return with_selected_course(
        clear_selected_course(state),
        course["id"],
        route=ROUTE_CHAT,
        course_name=course.get("name", ""),
    ), ""


def handle_open_responsible_course(state: dict[str, Any], course_id: str | None) -> tuple[dict[str, Any], str]:
    """Validate the selected responsible course and route the teacher to the course detail page."""
    if not is_logged_in(state) or user_role(state) != "teacher":
        return clear_selected_course(state), "Ikke tillatt."
    if not isinstance(course_id, str) or not course_id.strip():
        existing_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
        if state.get(ROUTE_KEY) == ROUTE_TEACHER_COURSE and existing_course_id:
            return state, ""
        return clear_selected_course(state), ""

    token = auth_token(state)
    if not token:
        return clear_selected_course(state), "Sessionen er utløpt — logg inn på nytt."

    courses, _err = _course_api.list_responsible_courses(token)
    course = next(
        (c for c in courses if isinstance(c, dict) and c.get("id") == course_id),
        None,
    )
    if course is None:
        return clear_selected_course(state), "Fant ikke faget."

    return with_selected_course(
        clear_selected_course(state),
        course["id"],
        route=ROUTE_TEACHER_COURSE,
        course_name=course.get("name", ""),
    ), ""
