"""Construction tests for chat page UI components."""

from __future__ import annotations

import gradio as gr

from src.ui.pages.chat_page import build_chat_page


def test_build_chat_page_assigns_scroll_hook_to_references_panel() -> None:
    with gr.Blocks():
        page = build_chat_page(visible=False)

    assert page.references_panel.elem_id == "chat-references-panel"
