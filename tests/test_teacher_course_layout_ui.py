"""Smoke tests for teacher course page composition."""

import gradio as gr

from src.ui.main_app import build_main_app
from src.ui.pages.teacher_course_page import (
    TEACHER_COURSE_TAB_STUDENTS,
    build_teacher_course_page,
    teacher_course_tabs_update,
)


def test_build_teacher_course_page_returns_nested_tab_components() -> None:
    with gr.Blocks():
        page = build_teacher_course_page(visible=False)

    assert page.tabs is not None
    assert page.back_button is not None
    assert page.view_as_student_button is not None
    assert page.students_tab.students_list is not None
    assert page.materials_tab.materials_list is not None
    assert page.instructions_tab.course_instructions_input is not None
    assert page.students_tab.status_text is not None
    assert page.materials_tab.status_text is not None
    assert page.instructions_tab.status_text is not None


def test_teacher_course_tabs_reset_to_students() -> None:
    update = teacher_course_tabs_update({})

    assert update.get("selected") == TEACHER_COURSE_TAB_STUDENTS


def test_build_main_app_smoke() -> None:
    app = build_main_app()

    assert app is not None
