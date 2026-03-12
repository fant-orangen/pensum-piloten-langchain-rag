"""Construction tests for chat page UI components."""

from __future__ import annotations

import gradio as gr

from src.ui.pages.chat_page import CHAT_PAGE_CSS, build_chat_page


def test_build_chat_page_assigns_reference_hooks() -> None:
    with gr.Blocks():
        page = build_chat_page(visible=False)

    assert page.references_panel.elem_id == "chat-references-panel"
    assert page.references_container.elem_id == "chat-references-column"
    assert page.open_references_button.elem_id == "chat-open-references-button"
    assert page.close_references_button.elem_id == "chat-close-references-button"
    assert page.message.elem_id == "chat-message-composer"


def test_chat_page_css_contains_reference_card_selectors() -> None:
    assert "#chat-references-column" in CHAT_PAGE_CSS
    assert "#chat-chat-column" in CHAT_PAGE_CSS
    assert ".chat-reference-entry" in CHAT_PAGE_CSS
