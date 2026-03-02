"""Teacher course page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.services import (
    add_student_to_course,
    get_addable_students_for_course,
    get_course,
    list_students_in_course,
)
from src.ui.state import COURSE_ID_KEY, USERNAME_KEY


@dataclass(slots=True)
class TeacherCoursePageComponents:
    group: gr.Group
    back_button: gr.Button
    course_title: gr.Markdown
    students_list: gr.Markdown
    add_student_username: gr.Dropdown
    add_student_button: gr.Button
    status_text: gr.Markdown


def build_teacher_course_page(*, visible: bool) -> TeacherCoursePageComponents:
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Fag")
        course_title = gr.Markdown("Fag: -")
        gr.Markdown("## Studenter")
        students_list = gr.Markdown("Ingen studenter ennå.")
        add_student_username = gr.Dropdown(
            choices=[],
            value=None,
            label="Studentbrukernavn",
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
    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    course = get_course(course_id)
    if course is None:
        return "Fag: -"
    return f"Fag: {course.name}"


def teacher_course_students_text(state: dict[str, Any]) -> str:
    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    students = list_students_in_course(course_id)
    if not students:
        return "Ingen studenter ennå."
    return "\n".join(f"- {student_username}" for student_username in students)


def teacher_course_student_choices_update(state: dict[str, Any], *, selected_username: str | None = None) -> Any:
    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    actor_username = str(state.get(USERNAME_KEY) or "").strip()
    choices = get_addable_students_for_course(course_id, actor_username)
    if selected_username and any(value == selected_username for _, value in choices):
        return gr.update(choices=choices, value=selected_username)
    return gr.update(choices=choices, value=None)


def handle_add_student(state: dict[str, Any], student_username: str | None) -> tuple[Any, str, str]:
    course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    actor_username = str(state.get(USERNAME_KEY) or "").strip()
    selected_username = student_username if isinstance(student_username, str) else ""
    success, message = add_student_to_course(course_id, selected_username, actor_username)
    next_input_update = teacher_course_student_choices_update(
        state,
        selected_username=None if success else selected_username,
    )
    return (
        next_input_update,
        teacher_course_students_text(state),
        message,
    )
