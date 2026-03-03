"""Student course page UI and helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.services import get_course
from src.ui.state import COURSE_ID_KEY


@dataclass(slots=True)
class StudentCoursePageComponents:
    group: gr.Group
    back_button: gr.Button
    course_title: gr.Markdown
    placeholder_text: gr.Markdown


def build_student_course_page(*, visible: bool) -> StudentCoursePageComponents:
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
    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    course = get_course(course_id)
    if course is None:
        return "Fag: -"
    return f"Fag: {course.name}"
