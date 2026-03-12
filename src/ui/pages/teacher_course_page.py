"""Teacher course page root UI and shared helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.pages.teacher_course_tabs.instructions_tab import (
    TeacherCourseInstructionsTabComponents,
    build_teacher_course_instructions_tab,
    handle_course_instructions_input,
    handle_save_course_instructions,
    teacher_course_instructions_updates,
    teacher_course_instructions_counter_update,
    teacher_course_instructions_input_update,
    teacher_course_instructions_status_update,
)
from src.ui.pages.teacher_course_tabs.materials_tab import (
    TeacherCourseMaterialsTabComponents,
    build_teacher_course_materials_tab,
    handle_delete_material,
    handle_refresh_ingestion,
    handle_start_ingestion,
    handle_upload_materials,
    teacher_course_ingestion_status_text,
    teacher_course_material_choices_update,
    teacher_course_material_status_update,
)
from src.ui.pages.teacher_course_tabs.students_tab import (
    TeacherCourseStudentsTabComponents,
    build_teacher_course_students_tab,
    handle_add_student,
    handle_import_students_csv,
    teacher_course_student_choices_update,
    teacher_course_student_import_file_update,
    teacher_course_student_import_results_update,
    teacher_course_student_status_update,
    teacher_course_students_text,
)
from src.ui.router import ROUTE_CHAT
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token, with_route

TEACHER_COURSE_TAB_STUDENTS = "teacher_course_students"
TEACHER_COURSE_TAB_MATERIALS = "teacher_course_materials"
TEACHER_COURSE_TAB_INSTRUCTIONS = "teacher_course_instructions"

__all__ = [
    "TEACHER_COURSE_TAB_STUDENTS",
    "TEACHER_COURSE_TAB_MATERIALS",
    "TEACHER_COURSE_TAB_INSTRUCTIONS",
    "TeacherCoursePageComponents",
    "build_teacher_course_page",
    "handle_add_student",
    "handle_course_instructions_input",
    "handle_delete_material",
    "handle_import_students_csv",
    "handle_refresh_ingestion",
    "handle_save_course_instructions",
    "handle_start_ingestion",
    "handle_upload_materials",
    "handle_view_as_student",
    "teacher_course_ingestion_status_text",
    "teacher_course_instructions_counter_update",
    "teacher_course_instructions_input_update",
    "teacher_course_instructions_status_update",
    "teacher_course_instructions_updates",
    "teacher_course_material_choices_update",
    "teacher_course_material_status_update",
    "teacher_course_student_choices_update",
    "teacher_course_student_import_file_update",
    "teacher_course_student_import_results_update",
    "teacher_course_student_status_update",
    "teacher_course_students_text",
    "teacher_course_tabs_update",
    "teacher_course_title_text",
]


@dataclass(slots=True)
class TeacherCoursePageComponents:
    group: gr.Group
    tabs: gr.Tabs
    back_button: gr.Button
    course_title: gr.Markdown
    view_as_student_button: gr.Button
    students_tab: TeacherCourseStudentsTabComponents
    materials_tab: TeacherCourseMaterialsTabComponents
    instructions_tab: TeacherCourseInstructionsTabComponents


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def teacher_course_tabs_update(_state: dict[str, Any]) -> Any:
    return gr.update(selected=TEACHER_COURSE_TAB_STUDENTS)


def build_teacher_course_page(*, visible: bool) -> TeacherCoursePageComponents:
    with gr.Group(visible=visible) as group:
        with gr.Row(equal_height=True):
            back_button = gr.Button("Tilbake", variant="secondary")
            course_title = gr.Markdown("Fag: -")
            view_as_student_button = gr.Button("Se som student", variant="secondary")

        with gr.Tabs(selected=TEACHER_COURSE_TAB_STUDENTS) as tabs:
            with gr.Tab("Studenter", id=TEACHER_COURSE_TAB_STUDENTS):
                students_tab = build_teacher_course_students_tab()
            with gr.Tab("Kursmateriale", id=TEACHER_COURSE_TAB_MATERIALS):
                materials_tab = build_teacher_course_materials_tab()
            with gr.Tab("Kursinstruksjoner", id=TEACHER_COURSE_TAB_INSTRUCTIONS):
                instructions_tab = build_teacher_course_instructions_tab()

    return TeacherCoursePageComponents(
        group=group,
        tabs=tabs,
        back_button=back_button,
        course_title=course_title,
        view_as_student_button=view_as_student_button,
        students_tab=students_tab,
        materials_tab=materials_tab,
        instructions_tab=instructions_tab,
    )


def teacher_course_title_text(state: dict[str, Any]) -> str:
    course_name = str(state.get(COURSE_NAME_KEY) or "").strip()
    if not course_name:
        course_id = _current_course_id(state)
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
    return f"Fag: {course_name}"


def handle_view_as_student(state: dict[str, Any]) -> tuple[dict[str, Any], str]:
    course_id = _current_course_id(state)
    if not course_id:
        return state, "Fant ikke faget."
    return with_route(state, ROUTE_CHAT), ""
