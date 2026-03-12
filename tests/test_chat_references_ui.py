"""Unit tests for chat references panel behavior."""

from __future__ import annotations

from types import SimpleNamespace

import src.ui.pages.chat_handlers as chat_page
import src.ui.pages.chat_handlers.references as reference_handlers
import src.ui.services.conversation_service as conversation_service


def _update_visible(update: object) -> bool | None:
    if isinstance(update, dict):
        return update.get("visible")
    return getattr(update, "visible", None)


def _assert_reference_block(
    panel: str,
    *,
    document: str,
    page: str | None,
    excerpt: str,
) -> None:
    assert f'<span class="chat-reference-document">{document}</span>' in panel
    assert f"Dokument:</strong> {document}" in panel
    assert f'<div class="chat-reference-excerpt">{excerpt}</div>' in panel
    if page is None:
        assert 'class="chat-reference-page"' not in panel
        assert "Side:</strong>" not in panel
    else:
        assert f'<span class="chat-reference-page">Side {page}</span>' in panel
        assert f"Side:</strong> {page}" in panel


def test_render_reference_panel_for_single_source() -> None:
    panel = chat_page._render_reference_panel_for_sources(
        [{"document": "doc1.pdf", "page": "4", "excerpt": "chunk"}]
    )

    _assert_reference_block(panel, document="doc1.pdf", page="4", excerpt="chunk")
    assert panel.count('<details class="chat-reference-entry">') == 1
    assert "<summary" in panel
    assert 'open="' not in panel
    assert "<hr" not in panel


def test_render_reference_panel_for_multiple_sources_renders_collapsible_cards() -> None:
    panel = chat_page._render_reference_panel_for_sources(
        [
            {"document": "doc1.pdf", "page": "4", "excerpt": "chunk 1"},
            {"document": "doc2.pdf", "page": "9", "excerpt": "chunk 2"},
        ]
    )

    _assert_reference_block(panel, document="doc1.pdf", page="4", excerpt="chunk 1")
    _assert_reference_block(panel, document="doc2.pdf", page="9", excerpt="chunk 2")
    assert panel.count('<details class="chat-reference-entry">') == 2
    assert panel.count('<summary class="chat-reference-summary">') == 2


def test_render_reference_panel_uses_fallbacks_for_missing_page_and_excerpt() -> None:
    panel = chat_page._render_reference_panel_for_sources(
        [{"document": "doc1.pdf", "page": "", "excerpt": ""}]
    )

    _assert_reference_block(
        panel,
        document="doc1.pdf",
        page=None,
        excerpt="Ingen tekst tilgjengelig.",
    )


def test_render_reference_panel_uses_cleaned_excerpt_text() -> None:
    normalized = conversation_service.normalize_sources_payload(
        [
            {
                "document": "<doc>.pdf",
                "page": "3",
                "excerpt": "<p>&Aring;pningslinje</p><script>bad()</script><br>linje 2",
            }
        ]
    )
    panel = chat_page._render_reference_panel_for_sources(normalized)

    assert "&lt;doc&gt;.pdf" in panel
    assert "<doc>.pdf" not in panel
    assert "bad()" not in panel
    assert "Åpningslinje<br>linje 2" in panel
    assert "&Aring;" not in panel
    assert "<script>" not in panel


def test_render_reference_panel_escapes_html_and_preserves_line_breaks() -> None:
    panel = chat_page._render_reference_panel_for_sources(
        [{"document": "<doc>.pdf", "page": "3", "excerpt": "<script>\nlinje 2"}]
    )

    assert "&lt;doc&gt;.pdf" in panel
    assert "&lt;script&gt;<br>linje 2" in panel
    assert "<script>" not in panel


def test_render_reference_panel_hides_page_badge_when_page_is_missing() -> None:
    panel = chat_page._render_reference_panel_for_sources(
        [{"document": "doc1.pdf", "page": "", "excerpt": "chunk"}]
    )

    _assert_reference_block(panel, document="doc1.pdf", page=None, excerpt="chunk")


def test_open_and_close_reference_layout_handlers_toggle_visibility() -> None:
    open_state, open_panel_update, open_button_update = chat_page._open_reference_layout_handler()
    close_state, close_panel_update, close_button_update = chat_page._close_reference_layout_handler()

    assert open_state is True
    assert close_state is False
    assert _update_visible(open_panel_update) is True
    assert _update_visible(open_button_update) is False
    assert _update_visible(close_panel_update) is False
    assert _update_visible(close_button_update) is True


def test_reference_layout_from_panel_handler_opens_for_populated_panel() -> None:
    is_open, panel_update, button_update = chat_page._reference_layout_from_panel_handler(
        "<div>panel</div>",
        "Kunne ikke hente kilder: timeout Viser lagrede referanser uten tekstutdrag.",
    )

    assert is_open is True
    assert _update_visible(panel_update) is True
    assert _update_visible(button_update) is False


def test_reference_layout_from_panel_handler_closes_for_empty_state() -> None:
    is_open, panel_update, button_update = chat_page._reference_layout_from_panel_handler(
        "",
        chat_page._REFERENCE_DEFAULT_STATUS,
    )

    assert is_open is False
    assert _update_visible(panel_update) is False
    assert _update_visible(button_update) is True


def test_chatbot_select_handler_populates_panel_for_assistant_message() -> None:
    source_history = [
        {"role": "user", "content": "Q1", "sources": []},
        {
            "role": "assistant",
            "content": "A1",
            "sources": [{"document": "doc1.pdf", "page": "4", "excerpt": "chunk"}],
        },
    ]
    evt = SimpleNamespace(index=1, selected=True)

    updated_history, panel, status = chat_page._chatbot_select_handler(
        source_history,
        None,
        chat_page._default_conversation_state(),
        evt,
    )

    assert updated_history == [
        {"message_id": None, "role": "user", "content": "Q1", "sources": []},
        {
            "message_id": None,
            "role": "assistant",
            "content": "A1",
            "sources": [{"document": "doc1.pdf", "page": "4", "excerpt": "chunk"}],
        },
    ]
    _assert_reference_block(panel, document="doc1.pdf", page="4", excerpt="chunk")
    assert status == "Viser 1 kildehenvisninger."


def test_chatbot_select_handler_user_message_clears_panel() -> None:
    source_history = [
        {"role": "user", "content": "Q1", "sources": []},
        {"role": "assistant", "content": "A1", "sources": []},
    ]
    evt = SimpleNamespace(index=0, selected=True)

    updated_history, panel, status = chat_page._chatbot_select_handler(
        source_history,
        None,
        chat_page._default_conversation_state(),
        evt,
    )

    assert updated_history == [
        {"message_id": None, "role": "user", "content": "Q1", "sources": []},
        {"message_id": None, "role": "assistant", "content": "A1", "sources": []},
    ]
    assert panel == ""
    assert status == "Kilder vises bare for tutorsvar."


def test_chatbot_select_handler_assistant_without_sources_shows_empty_state() -> None:
    source_history = [
        {"role": "assistant", "content": "A1", "sources": []},
    ]
    evt = SimpleNamespace(index=0, selected=True)

    updated_history, panel, status = chat_page._chatbot_select_handler(
        source_history,
        None,
        chat_page._default_conversation_state(),
        evt,
    )

    assert updated_history == [
        {"message_id": None, "role": "assistant", "content": "A1", "sources": []}
    ]
    assert panel == ""
    assert status == "Ingen kilder registrert for dette svaret."


def test_load_handler_auto_populates_latest_assistant_sources(monkeypatch) -> None:
    calls = {"get_sources": 0}

    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size
        if course_id == "course-1":
            return [
                {
                    "id": "conv-1",
                    "title": "Scoped",
                    "course_id": "course-1",
                    "updated_at": "2026-03-09T16:00",
                }
            ], 1, ""
        return [], 0, ""

    def _fake_get_messages(
        token: str,
        conversation_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ):
        del token, page, page_size
        if conversation_id != "conv-1":
            return [], 0, "missing"
        return [
            {
                "id": "msg-1",
                "role": "ai",
                "content": "A1",
                "sources": [{"document": "doc1.pdf", "page": "2", "excerpt": ""}],
            },
            {
                "id": "msg-0",
                "role": "human",
                "content": "Q1",
                "sources": [],
            },
        ], 2, ""

    def _fake_get_message_sources(token: str, conversation_id: str, message_id: str):
        assert token == "token-1"
        assert conversation_id == "conv-1"
        assert message_id == "msg-1"
        calls["get_sources"] += 1
        return [{"document": "doc1.pdf", "page": "2", "excerpt": "resolved chunk 1"}], ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(conversation_service, "get_messages", _fake_get_messages)
    monkeypatch.setattr(reference_handlers, "get_message_sources", _fake_get_message_sources)

    (
        _message,
        history,
        _status,
        conv_state,
        _selector,
        _count,
        source_history,
        ref_panel,
        ref_status,
    ) = chat_page._load_conversation_handler(
        conversation_id="conv-1",
        token="token-1",
        course_id="course-1",
    )

    assert history == [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
    ]
    assert calls["get_sources"] == 1
    assert conv_state["conversation_id"] == "conv-1"
    assert source_history[-1]["sources"] == [
        {"document": "doc1.pdf", "page": "2", "excerpt": "resolved chunk 1"}
    ]
    _assert_reference_block(ref_panel, document="doc1.pdf", page="2", excerpt="resolved chunk 1")
    assert ref_status == "Viser 1 kildehenvisninger."


def test_load_handler_latest_assistant_without_sources_shows_empty_state(monkeypatch) -> None:
    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size
        if course_id == "course-1":
            return [
                {
                    "id": "conv-1",
                    "title": "Scoped",
                    "course_id": "course-1",
                    "updated_at": "2026-03-09T16:00",
                }
            ], 1, ""
        return [], 0, ""

    def _fake_get_messages(
        token: str,
        conversation_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ):
        del token, page, page_size
        if conversation_id != "conv-1":
            return [], 0, "missing"
        return [
            {"id": "msg-1", "role": "ai", "content": "A1", "sources": []},
            {"id": "msg-0", "role": "human", "content": "Q1", "sources": []},
        ], 2, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(conversation_service, "get_messages", _fake_get_messages)

    (
        _message,
        _history,
        _status,
        _conv_state,
        _selector,
        _count,
        source_history,
        ref_panel,
        ref_status,
    ) = chat_page._load_conversation_handler(
        conversation_id="conv-1",
        token="token-1",
        course_id="course-1",
    )

    assert source_history[-1]["sources"] == []
    assert ref_panel == ""
    assert ref_status == "Ingen kilder registrert for dette svaret."


def test_load_handler_hydration_failure_falls_back_to_stored_references(monkeypatch) -> None:
    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size
        if course_id == "course-1":
            return [
                {
                    "id": "conv-1",
                    "title": "Scoped",
                    "course_id": "course-1",
                    "updated_at": "2026-03-09T16:00",
                }
            ], 1, ""
        return [], 0, ""

    def _fake_get_messages(
        token: str,
        conversation_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ):
        del token, page, page_size
        if conversation_id != "conv-1":
            return [], 0, "missing"
        return [
            {
                "id": "msg-1",
                "role": "ai",
                "content": "A1",
                "sources": [{"document": "doc1.pdf", "page": "2", "excerpt": ""}],
            },
            {"id": "msg-0", "role": "human", "content": "Q1", "sources": []},
        ], 2, ""

    def _fake_get_message_sources(token: str, conversation_id: str, message_id: str):
        del token, conversation_id, message_id
        return [], "Kunne ikke hente kilder: timeout"

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(conversation_service, "get_messages", _fake_get_messages)
    monkeypatch.setattr(reference_handlers, "get_message_sources", _fake_get_message_sources)

    (
        _message,
        _history,
        _status,
        _conv_state,
        _selector,
        _count,
        source_history,
        ref_panel,
        ref_status,
    ) = chat_page._load_conversation_handler(
        conversation_id="conv-1",
        token="token-1",
        course_id="course-1",
    )

    assert source_history[-1]["sources"] == [
        {"document": "doc1.pdf", "page": "2", "excerpt": ""}
    ]
    _assert_reference_block(ref_panel, document="doc1.pdf", page="2", excerpt="Ingen tekst tilgjengelig.")
    assert ref_status == "Kunne ikke hente kilder: timeout Viser lagrede referanser uten tekstutdrag."


def test_chat_handler_updates_reference_panel_from_ai_sources(monkeypatch) -> None:
    calls = {"get_sources": 0}

    def _fake_send_message(token: str, conversation_id: str, content: str):
        del token, conversation_id, content
        return True, "", {
            "id": "msg-1",
            "content": "A1",
            "sources": [{"document": "doc2.pdf", "page": "6", "excerpt": ""}],
        }

    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size
        if course_id == "course-1":
            return [
                {
                    "id": "conv-1",
                    "title": "Scoped",
                    "course_id": "course-1",
                    "updated_at": "2026-03-09T16:00",
                }
            ], 1, ""
        return [], 0, ""

    def _fake_get_message_sources(token: str, conversation_id: str, message_id: str):
        assert token == "token-1"
        assert conversation_id == "conv-1"
        assert message_id == "msg-1"
        calls["get_sources"] += 1
        return [{"document": "doc2.pdf", "page": "6", "excerpt": "resolved chunk 2"}], ""

    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(reference_handlers, "get_message_sources", _fake_get_message_sources)

    (
        _message,
        history,
        _status,
        _conv_state,
        _selector,
        _count,
        source_history,
        ref_panel,
        ref_status,
    ) = chat_page._chat_handler(
        user_message="Q1",
        history=[],
        source_history=[],
        conversation_state={"conversation_id": "conv-1", "title": "Scoped", "course_id": "course-1"},
        token="token-1",
        course_id_state="course-1",
    )

    assert history[-1] == {"role": "assistant", "content": "A1"}
    assert calls["get_sources"] == 1
    assert source_history[-1]["sources"] == [
        {"document": "doc2.pdf", "page": "6", "excerpt": "resolved chunk 2"}
    ]
    _assert_reference_block(ref_panel, document="doc2.pdf", page="6", excerpt="resolved chunk 2")
    assert ref_status == "Viser 1 kildehenvisninger."


def test_chatbot_select_handler_reuses_hydrated_sources_without_refetch(monkeypatch) -> None:
    calls = {"get_sources": 0}

    def _fake_get_message_sources(token: str, conversation_id: str, message_id: str):
        del token, conversation_id, message_id
        calls["get_sources"] += 1
        return [{"document": "doc1.pdf", "page": "4", "excerpt": "resolved"}], ""

    monkeypatch.setattr(reference_handlers, "get_message_sources", _fake_get_message_sources)

    source_history = [
        {"message_id": "msg-0", "role": "user", "content": "Q1", "sources": []},
        {
            "message_id": "msg-1",
            "role": "assistant",
            "content": "A1",
            "sources": [{"document": "doc1.pdf", "page": "4", "excerpt": "resolved"}],
        },
    ]
    evt = SimpleNamespace(index=1, selected=True)

    updated_history, panel, status = chat_page._chatbot_select_handler(
        source_history,
        "token-1",
        {"conversation_id": "conv-1", "title": "Scoped", "course_id": "course-1"},
        evt,
    )

    assert calls["get_sources"] == 0
    assert updated_history == source_history
    _assert_reference_block(panel, document="doc1.pdf", page="4", excerpt="resolved")
    assert status == "Viser 1 kildehenvisninger."


def test_chat_handler_auto_create_preserves_reference_panel_behavior(monkeypatch) -> None:
    calls = {"get_sources": 0}

    def _fake_create_conversation(token: str, course_id: str):
        assert token == "token-1"
        assert course_id == "course-1"
        return True, "", {"id": "conv-new", "title": "Ny samtale"}

    def _fake_send_message(token: str, conversation_id: str, content: str):
        assert token == "token-1"
        assert conversation_id == "conv-new"
        assert content == "Q1"
        return True, "", {
            "id": "msg-new",
            "content": "A1",
            "sources": [{"document": "doc3.pdf", "page": "9", "excerpt": ""}],
        }

    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size
        if course_id == "course-1":
            return [
                {
                    "id": "conv-new",
                    "title": "Ny samtale",
                    "course_id": "course-1",
                    "updated_at": "2026-03-09T16:00",
                }
            ], 1, ""
        return [], 0, ""

    def _fake_get_message_sources(token: str, conversation_id: str, message_id: str):
        assert token == "token-1"
        assert conversation_id == "conv-new"
        assert message_id == "msg-new"
        calls["get_sources"] += 1
        return [{"document": "doc3.pdf", "page": "9", "excerpt": "resolved chunk 3"}], ""

    monkeypatch.setattr(conversation_service, "create_conversation", _fake_create_conversation)
    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(reference_handlers, "get_message_sources", _fake_get_message_sources)

    (
        _message,
        history,
        _status,
        conv_state,
        _selector,
        _count,
        source_history,
        ref_panel,
        ref_status,
    ) = chat_page._chat_handler(
        user_message="Q1",
        history=[],
        source_history=[],
        conversation_state=chat_page._default_conversation_state(),
        token="token-1",
        course_id_state="course-1",
    )

    assert conv_state["conversation_id"] == "conv-new"
    assert history[-1] == {"role": "assistant", "content": "A1"}
    assert calls["get_sources"] == 1
    assert source_history[-1]["sources"] == [
        {"document": "doc3.pdf", "page": "9", "excerpt": "resolved chunk 3"}
    ]
    _assert_reference_block(ref_panel, document="doc3.pdf", page="9", excerpt="resolved chunk 3")
    assert ref_status == "Viser 1 kildehenvisninger."
