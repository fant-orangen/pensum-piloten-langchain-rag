"""Unit tests for teacher course ingestion UI handlers."""

from typing import Any

import src.ui.pages.teacher_course_page as teacher_course_page
from src.ui.state import COURSE_ID_KEY, TOKEN_KEY


def test_handle_start_ingestion_clears_selection_and_starts_staged_ingestion(monkeypatch) -> None:
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

    selection_update, status_text, message = teacher_course_page.handle_start_ingestion(
        state,
        ["material-a", " ", "material-b"],
    )

    assert selection_update.get("value") == []
    assert status_text == "status"
    assert message == "started"
    assert captured == {
        "token": "token-1",
        "course_id": "course-1",
        "material_ids": None,
    }


def test_teacher_course_ingestion_status_text_formats_summary(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-2",
        TOKEN_KEY: "token-2",
    }

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "list_ingestions",
        lambda _token, _course_id: (
            [
                {
                    "status": "building",
                    "rebuild_error": "no chunks",
                    "pending_additions": 3,
                    "pending_removals": 1,
                    "index_version": 7,
                    "active_scope": "scope-a",
                }
            ],
            "",
        ),
    )

    text = teacher_course_page.teacher_course_ingestion_status_text(state)
    assert "Status: Bygger indeks" in text
    assert "Venter på ingestering: 3" in text
    assert "Markert for sletting: 1" in text
    assert "Aktiv indeksversjon: 7" in text
    assert "Siste feil: no chunks" in text


def test_handle_delete_material_supports_multi_selection(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-3",
        TOKEN_KEY: "token-3",
    }
    captured: list[str] = []

    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_material_choices_update",
        lambda _state: "delete-update",
    )

    def _fake_delete_material(token: str, course_id: str, material_id: str) -> tuple[bool, str]:
        assert token == "token-3"
        assert course_id == "course-3"
        captured.append(material_id)
        return True, "deleted"

    monkeypatch.setattr(teacher_course_page._course_api, "delete_material", _fake_delete_material)

    delete_update, message = teacher_course_page.handle_delete_material(
        state,
        ["material-a", " ", "material-b"],
    )

    assert delete_update == "delete-update"
    assert message == "Slettet 2 materiale(r)."
    assert captured == ["material-a", "material-b"]


def test_material_choices_include_status_labels(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-4",
        TOKEN_KEY: "token-4",
    }
    monkeypatch.setattr(
        teacher_course_page._course_api,
        "list_materials",
        lambda _token, _course_id: (
            [
                {"id": "1", "original_filename": "a.pdf", "status": "pending_add", "size_bytes": 0},
                {"id": "2", "original_filename": "b.pdf", "status": "active", "size_bytes": 0},
                {"id": "3", "original_filename": "c.pdf", "status": "pending_remove", "size_bytes": 0},
            ],
            "",
        ),
    )

    update = teacher_course_page.teacher_course_material_choices_update(state)
    choice_labels = [label for label, _value in update.get("choices", [])]
    assert any(label.endswith("Venter på ingestering") for label in choice_labels)
    assert any(label.endswith("Ingestert") for label in choice_labels)
    assert any(label.endswith("Markert for sletting") for label in choice_labels)
