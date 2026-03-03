"""Teacher page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.services import (
    create_course,
    get_course,
    get_teacher_available_courses,
    get_teacher_responsible_courses,
)
from src.ui.router import ROUTE_TEACHER_COURSE
from src.ui.state import (
    COURSE_ID_KEY,
    NAME_KEY,
    ROUTE_KEY,
    USERNAME_KEY,
    clear_selected_course,
    is_logged_in,
    user_role,
    with_selected_course,
)


@dataclass(slots=True)
class TeacherPageComponents:
    group: gr.Group
    name_text: gr.Markdown
    responsible_list: gr.Radio
    available_list: gr.Markdown
    add_course_name: gr.Textbox
    add_course_button: gr.Button
    status_text: gr.Markdown
    logout_button: gr.Button


def _teacher_username(state: dict[str, Any]) -> str:
    return str(state.get(USERNAME_KEY) or "").strip()


def teacher_name_text(state: dict[str, Any]) -> str:
    name = str(state.get(NAME_KEY) or "").strip()
    return f"Navn: {name or '-'}"


def _render_course_lines(
    courses: list[Any],
    *,
    include_responsible: bool,
    empty_text: str,
) -> str:
    if not courses:
        return empty_text

    lines: list[str] = []
    for course in courses:
        if include_responsible:
            lines.append(f"- {course.name} (ansvarlig: {course.responsible_teacher_username})")
        else:
            lines.append(f"- {course.name}")
    return "\n".join(lines)


def teacher_responsible_courses_update(state: dict[str, Any]) -> Any:
    if not is_logged_in(state) or user_role(state) != "teacher":
        return gr.update(choices=[], value=None)

    courses = get_teacher_responsible_courses(_teacher_username(state))
    choices = [(course.name, course.course_id) for course in courses]
    selected_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
    if selected_course_id and any(course_id == selected_course_id for _, course_id in choices):
        return gr.update(choices=choices, value=selected_course_id)
    return gr.update(choices=choices, value=None)


def teacher_available_courses_text(state: dict[str, Any]) -> str:
    if not is_logged_in(state) or user_role(state) != "teacher":
        return "Ingen tilgjengelige fag."

    courses = get_teacher_available_courses(_teacher_username(state))
    return _render_course_lines(
        courses,
        include_responsible=True,
        empty_text="Ingen tilgjengelige fag.",
    )


def build_teacher_page(*, visible: bool) -> TeacherPageComponents:
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Lærer")
        name_text = gr.Markdown("Navn: -")
        gr.Markdown("## Ansvarlig for")
        responsible_list = gr.Radio(choices=[], value=None, label="Ansvarlig for")
        gr.Markdown("## Tilgjengelige fag")
        available_list = gr.Markdown("Ingen tilgjengelige fag.")
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


def handle_add_course(state: dict[str, Any], course_name: str) -> tuple[str, str, str, str]:
    if not is_logged_in(state) or user_role(state) != "teacher":
        return (
            course_name,
            teacher_responsible_courses_update(state),
            teacher_available_courses_text(state),
            "Ikke tillatt.",
        )

    _, message, _ = create_course(_teacher_username(state), course_name)
    next_input_value = "" if message == "Faget ble opprettet." else course_name
    return (
        next_input_value,
        teacher_responsible_courses_update(state),
        teacher_available_courses_text(state),
        message,
    )


def handle_open_teacher_course(state: dict[str, Any], course_id: str | None) -> tuple[dict[str, Any], str]:
    if not is_logged_in(state) or user_role(state) != "teacher":
        return clear_selected_course(state), "Ikke tillatt."
    if not isinstance(course_id, str) or not course_id.strip():
        existing_course_id = str(state.get(COURSE_ID_KEY) or "").strip()
        if state.get(ROUTE_KEY) == ROUTE_TEACHER_COURSE and existing_course_id:
            return state, ""
        return clear_selected_course(state), ""

    course = get_course(course_id)
    if course is None:
        return clear_selected_course(state), "Fant ikke faget."

    username = _teacher_username(state)
    if (
        username != course.responsible_teacher_username
        and username not in course.teacher_usernames
    ):
        return clear_selected_course(state), "Ikke tillatt."

    return with_selected_course(
        clear_selected_course(state),
        course.course_id,
        route=ROUTE_TEACHER_COURSE,
        course_name=course.name,
    ), ""
