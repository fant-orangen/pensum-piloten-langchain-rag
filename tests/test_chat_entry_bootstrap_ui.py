"""Unit tests for route-driven chat bootstrap behavior."""

from __future__ import annotations

from typing import Any

import src.ui.pages.chat_handlers as chat_page
import src.ui.services.conversation_service as conversation_service
import src.ui.services.course_service as course_service
from src.ui.router import ROUTE_CHAT


def _selector_choices(update: Any) -> list[tuple[str, str]]:
    if isinstance(update, dict):
        choices = update.get("choices", [])
    else:
        choices = getattr(update, "choices", [])
    return list(choices or [])


def test_bootstrap_chat_with_existing_course_loads_sidebar(monkeypatch) -> None:
    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size
        if course_id == "course-1":
            return [{"id": "conv-1", "title": "Scoped", "updated_at": "2026-03-09T16:00"}], 1, ""
        return [], 0, ""

    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    (
        _message,
        history,
        status,
        conv_state,
        selector_update,
        count_text,
        open_text,
        source_history,
        ref_rows,
        ref_status,
        resolved_course_id,
    ) = chat_page._bootstrap_chat_on_route_handler(
        route=ROUTE_CHAT,
        token="token-1",
        course_id_state="course-1",
    )

    assert history == []
    assert status == "Velg eller opprett en samtale først."
    assert conv_state == chat_page._default_conversation_state()
    assert len(_selector_choices(selector_update)) == 1
    assert count_text == "1 samtale funnet."
    assert open_text == "Åpen samtale: Ingen"
    assert source_history == []
    assert ref_rows == []
    assert ref_status == "Velg et tutorsvar for å se kilder."
    assert resolved_course_id == "course-1"


def test_bootstrap_chat_auto_selects_first_enrolled_course(monkeypatch) -> None:
    def _fake_list_courses(token: str):
        del token
        return [{"id": "course-2", "name": "X", "code": "X1"}], ""

    def _fake_list_conversations(
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        course_id: str | None = None,
    ):
        del token, page, page_size, course_id
        return [], 0, ""

    monkeypatch.setattr(course_service, "list_courses", _fake_list_courses)
    monkeypatch.setattr(conversation_service, "list_conversations", _fake_list_conversations)

    (
        _message,
        _history,
        status,
        _conv_state,
        selector_update,
        count_text,
        _open_text,
        _source_history,
        _ref_rows,
        _ref_status,
        resolved_course_id,
    ) = chat_page._bootstrap_chat_on_route_handler(
        route=ROUTE_CHAT,
        token="token-1",
        course_id_state=None,
    )

    assert status == "Fag valgt automatisk. Velg eller opprett en samtale først."
    assert _selector_choices(selector_update) == []
    assert count_text == "Ingen tidligere samtaler funnet."
    assert resolved_course_id == "course-2"


def test_bootstrap_chat_without_courses_shows_no_course_status(monkeypatch) -> None:
    def _fake_list_courses(token: str):
        del token
        return [], ""

    monkeypatch.setattr(course_service, "list_courses", _fake_list_courses)

    (
        _message,
        history,
        status,
        conv_state,
        selector_update,
        count_text,
        open_text,
        source_history,
        ref_rows,
        ref_status,
        resolved_course_id,
    ) = chat_page._bootstrap_chat_on_route_handler(
        route=ROUTE_CHAT,
        token="token-1",
        course_id_state=None,
    )

    assert history == []
    assert status == "Velg et fag før du bruker chat."
    assert conv_state == chat_page._default_conversation_state()
    assert _selector_choices(selector_update) == []
    assert count_text == "Ingen tidligere samtaler funnet."
    assert open_text == "Åpen samtale: Ingen"
    assert source_history == []
    assert ref_rows == []
    assert ref_status == "Velg et tutorsvar for å se kilder."
    assert resolved_course_id is None
