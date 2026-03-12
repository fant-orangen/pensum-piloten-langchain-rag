"""Construction tests for chat page UI components."""

from __future__ import annotations

import gradio as gr

from src.ui.pages.chat_page import (
    CHAT_PAGE_CSS,
    build_chat_page,
    chat_course_title_from_scope,
    chat_course_title_text,
)


def test_build_chat_page_assigns_reference_hooks() -> None:
    with gr.Blocks():
        page = build_chat_page(visible=False)

    assert page.course_title.elem_classes == ["chat-course-title"]
    assert page.sidebar_container.elem_id == "chat-sidebar-shell"
    assert page.sidebar_controls_container.elem_id == "chat-sidebar-controls"
    assert page.sidebar_conversations_container.elem_id == "chat-sidebar-list-section"
    assert page.conversation_list_container.elem_id == "chat-sidebar-list-container"
    assert page.conversation_selector.elem_id == "chat-conversation-selector"
    assert page.references_panel.elem_id == "chat-references-panel"
    assert page.references_container.elem_id == "chat-references-column"
    assert page.open_references_button_container.elem_id == "chat-open-references-button-container"
    assert page.open_references_button.elem_id == "chat-open-references-button"
    assert page.close_references_button.elem_id == "chat-close-references-button"
    assert page.conversation_count.elem_id == "chat-conversation-count"
    assert page.message.elem_id == "chat-message-composer"


def test_chat_page_css_contains_reference_card_selectors() -> None:
    assert "#chat-sidebar-shell" in CHAT_PAGE_CSS
    assert "#chat-sidebar-controls" in CHAT_PAGE_CSS
    assert "#chat-sidebar-list-container" in CHAT_PAGE_CSS
    assert "#chat-conversation-selector" in CHAT_PAGE_CSS
    assert "#chat-references-column" in CHAT_PAGE_CSS
    assert "#chat-chat-column" in CHAT_PAGE_CSS
    assert ".chat-course-title" in CHAT_PAGE_CSS
    assert "overflow-y: auto;" in CHAT_PAGE_CSS
    assert "max-height: 20rem;" in CHAT_PAGE_CSS
    assert "show_label=False" not in CHAT_PAGE_CSS
    assert "#chat-conversation-selector > label" in CHAT_PAGE_CSS
    assert "#chat-conversation-selector legend" in CHAT_PAGE_CSS
    assert "#chat-conversation-selector .wrap" in CHAT_PAGE_CSS
    assert "#chat-conversation-selector fieldset" in CHAT_PAGE_CSS
    assert ".chat-sidebar-list-section {\n    display: flex;\n    flex-direction: column;\n    gap: 0.75rem;\n    min-height: 0;\n    max-height: 44rem;" in CHAT_PAGE_CSS
    assert "#chat-sidebar-list-container {\n    display: flex;\n    flex-direction: column;\n    flex: 1;\n    min-height: 0;\n    overflow-x: hidden;\n    overflow-y: auto;" in CHAT_PAGE_CSS
    assert "#chat-conversation-selector .wrap {\n    overflow: visible;\n}" in CHAT_PAGE_CSS
    assert "height: 100%;" not in CHAT_PAGE_CSS.split("#chat-conversation-selector .wrap", 1)[1].split(".chat-conversation-summary", 1)[0]
    assert ".chat-reference-entry" in CHAT_PAGE_CSS


def test_chat_course_title_text_prefers_course_name_from_state() -> None:
    title = chat_course_title_text({"course_name": "INF101", "course_id": "course-1", "token": "token-1"})

    assert title == "## INF101"


def test_chat_course_title_from_scope_looks_up_course_name(monkeypatch) -> None:
    def _fake_list_courses(token: str):
        assert token == "token-1"
        return [{"id": "course-1", "name": "Algoritmer", "code": "INF201"}], ""

    monkeypatch.setattr("src.ui.services.course_service.list_courses", _fake_list_courses)

    assert chat_course_title_from_scope("token-1", "course-1") == "## Algoritmer"


def test_chat_course_title_text_falls_back_when_course_missing() -> None:
    assert chat_course_title_text({"course_id": None, "course_name": None, "token": None}) == "## Ingen fag valgt"
