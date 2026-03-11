"""Smoke tests for teacher landing page navigation styling."""

import gradio as gr

from src.ui.pages.teacher_page import TEACHER_PAGE_CSS, build_teacher_page


def test_teacher_page_course_lists_use_navigation_class() -> None:
    with gr.Blocks():
        page = build_teacher_page(visible=False)

    assert "teacher-course-nav" in (page.responsible_list.elem_classes or [])
    assert "teacher-course-nav" in (page.available_list.elem_classes or [])


def test_teacher_page_css_mentions_open_affordance() -> None:
    assert "teacher-course-nav" in TEACHER_PAGE_CSS
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in TEACHER_PAGE_CSS
    assert "@media (max-width: 1100px)" in TEACHER_PAGE_CSS
    assert "@media (max-width: 720px)" in TEACHER_PAGE_CSS
    assert 'content: "Åpne"' in TEACHER_PAGE_CSS
