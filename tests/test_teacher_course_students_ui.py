"""Unit tests for teacher course student listing and enrollment UI handlers."""

from typing import Any

import src.ui.pages.teacher_course_page as teacher_course_page
import src.ui.services.course_service as course_service
from src.ui.state import COURSE_ID_KEY, TOKEN_KEY


def test_teacher_course_students_text_uses_students_endpoint_shape(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-1",
        TOKEN_KEY: "token-1",
    }

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "list_course_students",
        lambda _token, _course_id: (
            [
                {
                    "id": "student-1",
                    "email": "ada@example.com",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                }
            ],
            "",
        ),
    )

    text = teacher_course_page.teacher_course_students_text(state)

    assert text == "- Student: Ada Lovelace (ada@example.com)"


def test_handle_add_student_refreshes_student_list_after_success(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-2",
        TOKEN_KEY: "token-2",
    }
    captured: dict[str, Any] = {}

    def _fake_enroll_user(
        token: str,
        course_id: str,
        user_email: str,
        *,
        role: str = "student",
    ) -> tuple[bool, str]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["user_email"] = user_email
        captured["role"] = role
        return True, "Bruker lagt til i faget."

    monkeypatch.setattr(teacher_course_page._course_api, "enroll_user", _fake_enroll_user)
    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_students_text",
        lambda _state: "- Student: Ada Lovelace (ada@example.com)",
    )

    input_update, students_text, message = teacher_course_page.handle_add_student(
        state,
        "ada@example.com",
    )

    assert captured == {
        "token": "token-2",
        "course_id": "course-2",
        "user_email": "ada@example.com",
        "role": "student",
    }
    assert input_update.get("value") == ""
    assert students_text == "- Student: Ada Lovelace (ada@example.com)"
    assert message == "Bruker lagt til i faget."


def test_list_course_students_extracts_paginated_items(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_get(path: str, *, token: str | None = None) -> Any:
        captured["path"] = path
        captured["token"] = token
        return {
            "items": [
                {
                    "id": "student-1",
                    "email": "ada@example.com",
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 100,
            "pages": 1,
        }

    monkeypatch.setattr(course_service, "get", _fake_get)

    students, error = course_service.list_course_students("token-3", "course-3")

    assert error == ""
    assert students == [
        {
            "id": "student-1",
            "email": "ada@example.com",
            "first_name": "Ada",
            "last_name": "Lovelace",
        }
    ]
    assert captured == {
        "path": "/courses/course-3/students?page=1&page_size=100",
        "token": "token-3",
    }
