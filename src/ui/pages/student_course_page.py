"""Student course page UI and helpers.

Provides the course detail view shown to students after selecting a course,
and resolves the display title from app state or the course API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token


@dataclass(slots=True)
class StudentCoursePageComponents:
    """Holds references to every Gradio component on the student course detail page."""

    group: gr.Group
    back_button: gr.Button
    course_title: gr.Markdown
    placeholder_text: gr.Markdown


def build_student_course_page(*, visible: bool) -> StudentCoursePageComponents:
    """Build and return the student course detail Gradio group."""
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Fag")
        course_title = gr.Markdown("Fag: -")
        placeholder_text = gr.Markdown("Mer kommer.")
        back_button = gr.Button("Tilbake")

    return StudentCoursePageComponents(
        group=group,
        back_button=back_button,
        course_title=course_title,
        placeholder_text=placeholder_text,
    )


def student_course_title_text(state: dict[str, Any]) -> str:
    """Resolve and return the display title for the current course, falling back to the API if the name is absent from state."""
    course_name = str(state.get(COURSE_NAME_KEY) or "").strip()
    if course_name:
        return f"Fag: {course_name}"

    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if not course_id:
        return "Fag: -"

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
