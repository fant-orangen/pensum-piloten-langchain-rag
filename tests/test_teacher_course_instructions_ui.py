"""Unit tests for teacher course instructions UI handlers."""

from typing import Any

import src.ui.pages.teacher_course_page as teacher_course_page
from src.ui.state import COURSE_ID_KEY, TOKEN_KEY


def test_handle_course_instructions_input_shows_live_counter() -> None:
    counter = teacher_course_page.handle_course_instructions_input("abc")
    assert counter == "Tegn brukt: 3/3000"


def test_handle_save_course_instructions_requires_course_id() -> None:
    state: dict[str, Any] = {TOKEN_KEY: "token-1"}
    input_update, counter, message = teacher_course_page.handle_save_course_instructions(
        state,
        "abc",
    )

    assert input_update.get("value") == "abc"
    assert counter == "Tegn brukt: 3/3000"
    assert message == "Fant ikke faget."


def test_handle_save_course_instructions_requires_token() -> None:
    state: dict[str, Any] = {COURSE_ID_KEY: "course-1"}
    input_update, counter, message = teacher_course_page.handle_save_course_instructions(
        state,
        "abc",
    )

    assert input_update.get("value") == "abc"
    assert counter == "Tegn brukt: 3/3000"
    assert message == "Sessionen er utløpt — logg inn på nytt."


def test_handle_save_course_instructions_rejects_too_long_input(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-1",
        TOKEN_KEY: "token-1",
    }
    too_long = "x" * (teacher_course_page.MAX_COURSE_INSTRUCTIONS_CHARS + 1)

    def _should_not_call(*_args: Any, **_kwargs: Any) -> tuple[bool, str, dict[str, Any] | None]:
        raise AssertionError("API should not be called when input exceeds max length.")

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "update_course_instructions",
        _should_not_call,
    )

    input_update, counter, message = teacher_course_page.handle_save_course_instructions(
        state,
        too_long,
    )

    assert input_update.get("value") == too_long
    assert counter == f"Tegn brukt: {len(too_long)}/3000"
    assert message == "Instruksjonene er for lange. Maks 3000 tegn."


def test_handle_save_course_instructions_trims_and_saves(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-2",
        TOKEN_KEY: "token-2",
    }
    captured: dict[str, Any] = {}

    def _fake_update_course_instructions(
        token: str,
        course_id: str,
        instructions: str | None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["instructions"] = instructions
        return True, "lagret", {"id": "course-2"}

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "update_course_instructions",
        _fake_update_course_instructions,
    )

    input_update, counter, message = teacher_course_page.handle_save_course_instructions(
        state,
        "  Bruk korte svar  ",
    )

    assert captured == {
        "token": "token-2",
        "course_id": "course-2",
        "instructions": "Bruk korte svar",
    }
    assert input_update.get("value") == "Bruk korte svar"
    assert counter == "Tegn brukt: 15/3000"
    assert message == "lagret"


def test_handle_save_course_instructions_empty_text_clears_value(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-3",
        TOKEN_KEY: "token-3",
    }
    captured: dict[str, Any] = {}

    def _fake_update_course_instructions(
        token: str,
        course_id: str,
        instructions: str | None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["instructions"] = instructions
        return True, "tømt", {"id": "course-3"}

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "update_course_instructions",
        _fake_update_course_instructions,
    )

    input_update, counter, message = teacher_course_page.handle_save_course_instructions(
        state,
        "   ",
    )

    assert captured == {
        "token": "token-3",
        "course_id": "course-3",
        "instructions": None,
    }
    assert input_update.get("value") == ""
    assert counter == "Tegn brukt: 0/3000"
    assert message == "tømt"


def test_handle_save_course_instructions_keeps_raw_input_on_api_error(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-4",
        TOKEN_KEY: "token-4",
    }
    captured: dict[str, Any] = {}

    def _fake_update_course_instructions(
        token: str,
        course_id: str,
        instructions: str | None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["instructions"] = instructions
        return False, "feilet", None

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "update_course_instructions",
        _fake_update_course_instructions,
    )

    raw_value = "  hold dette  "
    input_update, counter, message = teacher_course_page.handle_save_course_instructions(
        state,
        raw_value,
    )

    assert captured == {
        "token": "token-4",
        "course_id": "course-4",
        "instructions": "hold dette",
    }
    assert input_update.get("value") == raw_value
    assert counter == f"Tegn brukt: {len(raw_value)}/3000"
    assert message == "feilet"
