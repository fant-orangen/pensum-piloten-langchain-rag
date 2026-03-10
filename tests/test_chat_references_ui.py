"""Unit tests for chat references panel behavior."""

from __future__ import annotations

from types import SimpleNamespace

import src.ui.pages.chat_handlers as chat_page
import src.ui.services.conversation_service as conversation_service


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

    rows, status = chat_page._chatbot_select_handler(source_history, evt)

    assert rows == [["doc1.pdf", "4", "chunk"]]
    assert status == "Viser 1 kildehenvisninger."


def test_chatbot_select_handler_user_message_clears_panel() -> None:
    source_history = [
        {"role": "user", "content": "Q1", "sources": []},
        {"role": "assistant", "content": "A1", "sources": []},
    ]
    evt = SimpleNamespace(index=0, selected=True)

    rows, status = chat_page._chatbot_select_handler(source_history, evt)

    assert rows == []
    assert status == "Kilder vises bare for tutorsvar."


def test_chatbot_select_handler_assistant_without_sources_shows_empty_state() -> None:
    source_history = [
        {"role": "assistant", "content": "A1", "sources": []},
    ]
    evt = SimpleNamespace(index=0, selected=True)

    rows, status = chat_page._chatbot_select_handler(source_history, evt)

    assert rows == []
    assert status == "Ingen kilder registrert for dette svaret."


def test_load_handler_auto_populates_latest_assistant_sources(monkeypatch) -> None:
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
                "role": "ai",
                "content": "A1",
                "sources": [{"document": "doc1.pdf", "page": "2", "excerpt": "chunk 1"}],
            },
            {
                "role": "human",
                "content": "Q1",
                "sources": [],
            },
        ], 2, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(conversation_service, "get_messages", _fake_get_messages)

    (
        _message,
        history,
        _status,
        conv_state,
        _selector,
        _count,
        _open,
        source_history,
        ref_rows,
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
    assert conv_state["conversation_id"] == "conv-1"
    assert source_history[-1]["sources"] == [
        {"document": "doc1.pdf", "page": "2", "excerpt": "chunk 1"}
    ]
    assert ref_rows == [["doc1.pdf", "2", "chunk 1"]]
    assert ref_status == "Viser 1 kildehenvisninger."


def test_chat_handler_updates_reference_panel_from_ai_sources(monkeypatch) -> None:
    def _fake_send_message(token: str, conversation_id: str, content: str):
        del token, conversation_id, content
        return True, "", {
            "content": "A1",
            "sources": [{"document": "doc2.pdf", "page": "6", "excerpt": "chunk 2"}],
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

    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    (
        _message,
        history,
        _status,
        _conv_state,
        _selector,
        _count,
        _open,
        source_history,
        ref_rows,
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
    assert source_history[-1]["sources"] == [
        {"document": "doc2.pdf", "page": "6", "excerpt": "chunk 2"}
    ]
    assert ref_rows == [["doc2.pdf", "6", "chunk 2"]]
    assert ref_status == "Viser 1 kildehenvisninger."


def test_chat_handler_auto_create_preserves_reference_panel_behavior(monkeypatch) -> None:
    def _fake_create_conversation(token: str, course_id: str):
        assert token == "token-1"
        assert course_id == "course-1"
        return True, "", {"id": "conv-new", "title": "Ny samtale"}

    def _fake_send_message(token: str, conversation_id: str, content: str):
        assert token == "token-1"
        assert conversation_id == "conv-new"
        assert content == "Q1"
        return True, "", {
            "content": "A1",
            "sources": [{"document": "doc3.pdf", "page": "9", "excerpt": "chunk 3"}],
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

    monkeypatch.setattr(conversation_service, "create_conversation", _fake_create_conversation)
    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    (
        _message,
        history,
        _status,
        conv_state,
        _selector,
        _count,
        _open,
        source_history,
        ref_rows,
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
    assert source_history[-1]["sources"] == [
        {"document": "doc3.pdf", "page": "9", "excerpt": "chunk 3"}
    ]
    assert ref_rows == [["doc3.pdf", "9", "chunk 3"]]
    assert ref_status == "Viser 1 kildehenvisninger."
