"""Regression tests for chat UI scope isolation (user + course)."""

from typing import Any

import src.ui.pages.chat_handlers as chat_page
import src.ui.services.conversation_service as conversation_service


def _selector_value(update: Any) -> Any:
    if isinstance(update, dict):
        return update.get("value")
    return getattr(update, "value", None)


def test_chat_handler_blocks_send_when_no_course_selected(monkeypatch) -> None:
    calls = {"send": 0}

    def _fake_send_message(token: str, conversation_id: str, content: str):
        del token, conversation_id, content
        calls["send"] += 1
        return True, "", {"content": "ok"}

    def _fake_list_conversations(token: str, *, page: int = 1, page_size: int = 20, course_id: str | None = None):
        del token, page, page_size, course_id
        return [], 0, ""

    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    _message, _history, status, conv_state, _selector, _count, _source_history, _ref_rows, _ref_status = chat_page._chat_handler(
        user_message="hello",
        history=[],
        source_history=[],
        conversation_state={"conversation_id": "conv-1", "title": "Old", "course_id": "course-1"},
        token="token-1",
        course_id_state=None,
    )

    assert calls["send"] == 0
    assert status == "Velg et fag før du bruker chat."
    assert conv_state == chat_page._default_conversation_state()


def test_chat_handler_blocks_stale_conversation_course_mismatch(monkeypatch) -> None:
    calls = {"send": 0}

    def _fake_send_message(token: str, conversation_id: str, content: str):
        del token, conversation_id, content
        calls["send"] += 1
        return True, "", {"content": "ok"}

    def _fake_list_conversations(token: str, *, page: int = 1, page_size: int = 20, course_id: str | None = None):
        del token, page, page_size
        if course_id == "course-2":
            return [{"id": "conv-2", "title": "New", "course_id": "course-2", "updated_at": "2026-03-09"}], 1, ""
        return [], 0, ""

    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    _message, _history, status, conv_state, _selector, _count, _source_history, _ref_rows, _ref_status = chat_page._chat_handler(
        user_message="hello",
        history=[],
        source_history=[],
        conversation_state={"conversation_id": "conv-1", "title": "Old", "course_id": "course-1"},
        token="token-1",
        course_id_state="course-2",
    )

    assert calls["send"] == 0
    assert status == "Samtalen er ikke i aktivt fag. Velg eller opprett en ny samtale."
    assert conv_state == chat_page._default_conversation_state()


def test_load_handler_accepts_only_conversations_in_active_course_scope(monkeypatch) -> None:
    calls = {"get_messages": 0}

    def _fake_list_conversations(token: str, *, page: int = 1, page_size: int = 20, course_id: str | None = None):
        del token, page, page_size
        if course_id == "course-2":
            return [{"id": "conv-2", "title": "Only Here", "course_id": "course-2", "updated_at": "2026-03-09"}], 1, ""
        return [], 0, ""

    def _fake_get_messages(token: str, conversation_id: str, *, page: int = 1, page_size: int = 50):
        del token, conversation_id, page, page_size
        calls["get_messages"] += 1
        return [], 0, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(conversation_service, "get_messages", _fake_get_messages)

    _message, _history, status, conv_state, _selector, _count, _source_history, _ref_rows, _ref_status = chat_page._load_conversation_handler(
        conversation_id="conv-1",
        token="token-1",
        course_id="course-2",
    )

    assert calls["get_messages"] == 0
    assert status == "Samtalen er ikke i aktivt fag. Velg eller opprett en ny samtale."
    assert conv_state == chat_page._default_conversation_state()


def test_refresh_handler_clears_invalid_selected_conversation(monkeypatch) -> None:
    def _fake_list_conversations(token: str, *, page: int = 1, page_size: int = 20, course_id: str | None = None):
        del token, page, page_size
        if course_id == "course-1":
            return [{"id": "conv-2", "title": "Scoped", "course_id": "course-1", "updated_at": "2026-03-09"}], 1, ""
        return [], 0, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    selector_update, _count, status, conv_state, _source_history, _ref_rows, _ref_status = chat_page._refresh_handler(
        conversation_state={"conversation_id": "conv-1", "title": "Old", "course_id": "course-1"},
        source_history=[],
        token="token-1",
        course_id_state="course-1",
    )

    assert _selector_value(selector_update) is None
    assert status == "Samtalelisten er oppdatert."
    assert conv_state == chat_page._default_conversation_state()


def test_chat_handler_auto_creates_conversation_when_missing(monkeypatch) -> None:
    calls = {"create": 0, "send": 0}

    def _fake_create_conversation(token: str, course_id: str):
        assert token == "token-1"
        assert course_id == "course-1"
        calls["create"] += 1
        return True, "", {"id": "conv-new", "title": "Ny samtale"}

    def _fake_send_message(token: str, conversation_id: str, content: str):
        assert token == "token-1"
        assert conversation_id == "conv-new"
        assert content == "hello"
        calls["send"] += 1
        return True, "", {"content": "ok", "sources": []}

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
                {"id": "conv-new", "title": "Ny samtale", "course_id": "course-1", "updated_at": "2026-03-09"}
            ], 1, ""
        return [], 0, ""

    monkeypatch.setattr(conversation_service, "create_conversation", _fake_create_conversation)
    monkeypatch.setattr(conversation_service, "send_message", _fake_send_message)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    _message, history, _status, conv_state, _selector, _count, _source_history, _ref_rows, _ref_status = chat_page._chat_handler(
        user_message="hello",
        history=[],
        source_history=[],
        conversation_state=chat_page._default_conversation_state(),
        token="token-1",
        course_id_state="course-1",
    )

    assert calls["create"] == 1
    assert calls["send"] == 1
    assert conv_state["conversation_id"] == "conv-new"
    assert history[-1] == {"role": "assistant", "content": "ok"}
