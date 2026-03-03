"""Teacher course page UI and handlers.

Provides the course detail view for teachers, including the ability to enrol
students in the selected course by e-mail address.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token


@dataclass(slots=True)
class TeacherCoursePageComponents:
    """Holds references to every Gradio component on the teacher course detail page."""

    group: gr.Group
    back_button: gr.Button
    course_title: gr.Markdown
    students_list: gr.Markdown
    add_student_username: gr.Textbox
    add_student_button: gr.Button
    status_text: gr.Markdown


def build_teacher_course_page(*, visible: bool) -> TeacherCoursePageComponents:
    """Build and return the teacher course detail Gradio group."""
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Fag")
        course_title = gr.Markdown("Fag: -")
        gr.Markdown("## Studenter")
        students_list = gr.Markdown("Ingen studenter ennå.")
        add_student_username = gr.Textbox(
            label="Studentens e-post",
            placeholder="student@example.com",
        )
        add_student_button = gr.Button("Legg til student", variant="primary")
        status_text = gr.Markdown()
        back_button = gr.Button("Tilbake")

    return TeacherCoursePageComponents(
        group=group,
        back_button=back_button,
        course_title=course_title,
        students_list=students_list,
        add_student_username=add_student_username,
        add_student_button=add_student_button,
        status_text=status_text,
    )


def teacher_course_title_text(state: dict[str, Any]) -> str:
    """Resolve and return the display title for the current course, falling back to the API if needed."""
    course_name = str(state.get(COURSE_NAME_KEY) or "").strip()
    if not course_name:
        course_id = str(state.get(COURSE_ID_KEY) or "").strip()
        if not course_id:
            return "Fag: -"
        # Fall back to fetching from API if course_name is not in state.
        token = auth_token(state)
        if not token:
            return "Fag: -"
        courses, _err = _course_api.list_courses(token)
        course = next(
            (c for c in courses if isinstance(c, dict) and c.get("id") == course_id),
            None,
        )
        if course is None:
            return "Fag: -"
        return f"Fag: {course.get('name', '-')}"
    return f"Fag: {course_name}"


def teacher_course_students_text(state: dict[str, Any]) -> str:
    """Return a placeholder message for the student list until the enrollments endpoint is available."""
    # The API does not expose a student-listing endpoint; the enrolled users
    # are managed through /courses/{id}/enrollments. Without a GET enrollments
    # endpoint this list cannot be populated from the API yet.
    # TODO: implement GET /courses/{id}/enrollments once that endpoint exists.
    return "Studentliste er ikke tilgjengelig via API ennå."


def teacher_course_student_choices_update(state: dict[str, Any], *, selected_username: str | None = None) -> Any:
    """Return a Gradio update for the student input field, preserving any pre-selected username."""
    # The API does not expose a list-of-addable-students endpoint.
    # The text input field is used instead of a dropdown.
    # TODO: implement once GET /users (student list) endpoint exists.
    return gr.update(value=selected_username or "")


def handle_add_student(state: dict[str, Any], student_email: str | None) -> tuple[Any, str, str]:
    """Enrol the given student e-mail in the currently selected course and refresh the student list."""
    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if not course_id:
        return gr.update(value=""), teacher_course_students_text(state), "Fant ikke faget."

    token = auth_token(state)
    if not token:
        return gr.update(value=""), teacher_course_students_text(state), "Sessionen er utløpt — logg inn på nytt."

    email = (student_email or "").strip()
    if not email:
        return gr.update(value=""), teacher_course_students_text(state), "Fyll ut e-postadressen."

    success, message = _course_api.enroll_user(token, course_id, email, role="student")
    next_input_value = "" if success else email
    return (
        gr.update(value=next_input_value),
        teacher_course_students_text(state),
        message,
    )
