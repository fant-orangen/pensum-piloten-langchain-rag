"""Unit tests for teacher course ingestion UI handlers."""

from typing import Any

import src.ui.pages.teacher_course_page as teacher_course_page
from src.ui.state import COURSE_ID_KEY, TOKEN_KEY


def test_handle_start_ingestion_forwards_selected_material_ids(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-1",
        TOKEN_KEY: "token-1",
    }
    captured: dict[str, Any] = {}

    def _fake_start_ingestion(
        token: str,
        course_id: str,
        *,
        material_ids: list[str] | None = None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["material_ids"] = material_ids
        return True, "started", {"id": "job-1"}

    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_ingestion_status_text",
        lambda _state: "status",
    )
    monkeypatch.setattr(teacher_course_page._course_api, "start_ingestion", _fake_start_ingestion)

    status_text, message = teacher_course_page.handle_start_ingestion(
        state,
        ["material-a", " ", "material-b"],
    )

    assert status_text == "status"
    assert message == "started"
    assert captured == {
        "token": "token-1",
        "course_id": "course-1",
        "material_ids": ["material-a", "material-b"],
    }


def test_handle_start_ingestion_without_selection_uses_all_materials(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-2",
        TOKEN_KEY: "token-2",
    }
    captured: dict[str, Any] = {}

    def _fake_start_ingestion(
        token: str,
        course_id: str,
        *,
        material_ids: list[str] | None = None,
    ) -> tuple[bool, str, dict[str, Any] | None]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["material_ids"] = material_ids
        return True, "started all", {"id": "job-2"}

    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_ingestion_status_text",
        lambda _state: "status-all",
    )
    monkeypatch.setattr(teacher_course_page._course_api, "start_ingestion", _fake_start_ingestion)

    status_text, message = teacher_course_page.handle_start_ingestion(state, [])

    assert status_text == "status-all"
    assert message == "started all"
    assert captured["material_ids"] is None


def test_handle_delete_material_keeps_single_selected_id(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-3",
        TOKEN_KEY: "token-3",
    }
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_material_choices_update",
        lambda _state: "delete-update",
    )
    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_ingestion_material_choices_update",
        lambda _state: "ingestion-update",
    )

    def _fake_delete_material(token: str, course_id: str, material_id: str) -> tuple[bool, str]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["material_id"] = material_id
        return True, "deleted"

    monkeypatch.setattr(teacher_course_page._course_api, "delete_material", _fake_delete_material)

    delete_update, ingestion_update, message = teacher_course_page.handle_delete_material(
        state,
        "material-single",
    )

    assert delete_update == "delete-update"
    assert ingestion_update == "ingestion-update"
    assert message == "deleted"
    assert captured["material_id"] == "material-single"
