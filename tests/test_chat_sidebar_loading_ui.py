"""Tests for full conversation loading in the chat sidebar."""

from __future__ import annotations

from typing import Any

import src.ui.pages.chat_handlers as chat_page
import src.ui.services.chat_orchestration_service as orchestration_service
import src.ui.services.conversation_service as conversation_service


def _selector_choices(update: Any) -> list[tuple[str, str]]:
    if isinstance(update, dict):
        choices = update.get("choices", [])
    else:
        choices = getattr(update, "choices", [])
    return list(choices or [])


def _selector_value(update: Any) -> Any:
    if isinstance(update, dict):
        return update.get("value")
    return getattr(update, "value", None)


def test_fetch_conversations_aggregates_all_pages(monkeypatch) -> None:
    calls: list[tuple[int, int, str | None]] = []

    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        assert token == "token-1"
        calls.append((page, page_size, course_id))
        if page == 1:
            return (
                [{"id": "conv-3", "title": "Newest", "updated_at": "2026-03-12T10:00"}],
                3,
                "",
            )
        if page == 2:
            return (
                [
                    {"id": "conv-2", "title": "Middle", "updated_at": "2026-03-11T10:00"},
                    {"id": "conv-1", "title": "Oldest", "updated_at": "2026-03-10T10:00"},
                ],
                3,
                "",
            )
        return [], 3, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    items, total, err = orchestration_service.fetch_conversations(
        "token-1",
        "course-1",
        no_course_status="no course",
    )

    assert err == ""
    assert total == 3
    assert [item["id"] for item in items] == ["conv-3", "conv-2", "conv-1"]
    assert calls == [(1, 100, "course-1"), (2, 100, "course-1")]


def test_build_sidebar_model_uses_total_count_across_pages(monkeypatch) -> None:
    def _fake_fetch_conversations(
        token: str,
        course_id: str | None,
        *,
        no_course_status: str,
    ):
        assert token == "token-1"
        assert course_id == "course-1"
        assert no_course_status == "Velg et fag før du bruker chat."
        return (
            [
                {"id": "conv-3", "title": "Newest", "updated_at": "2026-03-12T10:00"},
                {"id": "conv-2", "title": "Middle", "updated_at": "2026-03-11T10:00"},
                {"id": "conv-1", "title": "Oldest", "updated_at": "2026-03-10T10:00"},
            ],
            3,
            "",
        )

    monkeypatch.setattr(orchestration_service, "fetch_conversations", _fake_fetch_conversations)

    model = orchestration_service.build_sidebar_model(
        "token-1",
        course_id="course-1",
        selected_id="conv-1",
        status_message="",
        no_course_status="Velg et fag før du bruker chat.",
    )

    assert model["count"] == 3
    assert model["selected_id"] == "conv-1"
    assert [value for _label, value in model["choices"]] == ["conv-3", "conv-2", "conv-1"]


def test_load_handler_accepts_conversation_from_later_page(monkeypatch) -> None:
    calls = {"get_messages": 0}

    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token
        assert course_id == "course-1"
        assert page_size == 100
        if page == 1:
            return (
                [{"id": "conv-3", "title": "Newest", "course_id": "course-1", "updated_at": "2026-03-12T10:00"}],
                3,
                "",
            )
        if page == 2:
            return (
                [
                    {"id": "conv-2", "title": "Middle", "course_id": "course-1", "updated_at": "2026-03-11T10:00"},
                    {"id": "conv-1", "title": "Oldest", "course_id": "course-1", "updated_at": "2026-03-10T10:00"},
                ],
                3,
                "",
            )
        return [], 3, ""

    def _fake_get_messages(token: str, conversation_id: str, *, page: int = 1, page_size: int = 50):
        del token, page, page_size
        calls["get_messages"] += 1
        assert conversation_id == "conv-1"
        return [
            {"id": "msg-1", "role": "ai", "content": "Svar"},
            {"id": "msg-0", "role": "human", "content": "Spm"},
        ], 2, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)
    monkeypatch.setattr(conversation_service, "get_messages", _fake_get_messages)

    (
        _message,
        history,
        status,
        conv_state,
        selector_update,
        count_text,
    ) = chat_page._load_conversation_handler(
        conversation_id="conv-1",
        token="token-1",
        course_id="course-1",
    )

    assert calls["get_messages"] == 1
    assert history == [{"role": "user", "content": "Spm"}, {"role": "assistant", "content": "Svar"}]
    assert status == ""
    assert conv_state["conversation_id"] == "conv-1"
    assert _selector_value(selector_update) == "conv-1"
    assert [value for _label, value in _selector_choices(selector_update)] == ["conv-3", "conv-2", "conv-1"]
    assert count_text == "3 samtaler funnet."
