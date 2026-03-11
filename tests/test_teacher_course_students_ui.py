"""Unit tests for teacher course student listing and enrollment UI handlers."""

from typing import Any
from pathlib import Path

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


def test_teacher_course_import_reset_helpers_clear_controls() -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-3",
        TOKEN_KEY: "token-3",
    }

    file_update = teacher_course_page.teacher_course_student_import_file_update(state)
    results_text = teacher_course_page.teacher_course_student_import_results_update(state)

    assert file_update.get("value") is None
    assert results_text == ""


def test_teacher_course_tabs_default_to_students() -> None:
    update = teacher_course_page.teacher_course_tabs_update({})

    assert update.get("selected") == teacher_course_page.TEACHER_COURSE_TAB_STUDENTS


def test_handle_import_students_csv_parses_header_and_bom(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-4",
        TOKEN_KEY: "token-4",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("\ufeffemail\nada@example.com\n", encoding="utf-8")
    captured: dict[str, Any] = {"emails": []}

    def _fake_enroll_user(
        token: str,
        course_id: str,
        user_email: str,
        *,
        role: str = "student",
    ) -> tuple[bool, str]:
        captured["token"] = token
        captured["course_id"] = course_id
        captured["emails"].append((user_email, role))
        return True, "Bruker lagt til i faget."

    monkeypatch.setattr(teacher_course_page._course_api, "enroll_user", _fake_enroll_user)
    monkeypatch.setattr(
        teacher_course_page,
        "teacher_course_students_text",
        lambda _state: "- Student: Ada Lovelace (ada@example.com)",
    )
    warnings: list[str] = []
    monkeypatch.setattr(teacher_course_page.gr, "Warning", warnings.append)

    file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert captured == {
        "token": "token-4",
        "course_id": "course-4",
        "emails": [("ada@example.com", "student")],
    }
    assert file_update.get("value") is None
    assert students_text == "- Student: Ada Lovelace (ada@example.com)"
    assert "- Importert: 1" in import_results
    assert "- Ikke registrert i appen: 0" in import_results
    assert message == "Import fullført."
    assert warnings == []


def test_handle_import_students_csv_ignores_blank_rows_and_duplicates(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-5",
        TOKEN_KEY: "token-5",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("email\n\nada@example.com\nADA@example.com \n", encoding="utf-8")
    captured: list[str] = []

    def _fake_enroll_user(
        _token: str,
        _course_id: str,
        user_email: str,
        *,
        role: str = "student",
    ) -> tuple[bool, str]:
        assert role == "student"
        captured.append(user_email)
        return True, "Bruker lagt til i faget."

    monkeypatch.setattr(teacher_course_page._course_api, "enroll_user", _fake_enroll_user)
    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")
    monkeypatch.setattr(teacher_course_page.gr, "Warning", lambda _message: None)

    _file_update, _students_text, import_results, _message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert captured == ["ada@example.com"]
    assert "- Importert: 1" in import_results
    assert "- Ugyldige rader: 0" in import_results


def test_handle_import_students_csv_reports_invalid_rows(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-6",
        TOKEN_KEY: "token-6",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("email\nnot-an-email\nada@example.com\n", encoding="utf-8")

    monkeypatch.setattr(
        teacher_course_page._course_api,
        "enroll_user",
        lambda *_args, **_kwargs: (True, "Bruker lagt til i faget."),
    )
    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")
    monkeypatch.setattr(teacher_course_page.gr, "Warning", lambda _message: None)

    _file_update, _students_text, import_results, _message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert "- Ugyldige rader: 1" in import_results
    assert "- Rad 2: ugyldig e-post 'not-an-email'." in import_results


def test_handle_import_students_csv_warns_and_lists_missing_users(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-7",
        TOKEN_KEY: "token-7",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("missing@example.com\nknown@example.com\n", encoding="utf-8")
    warnings: list[str] = []

    def _fake_enroll_user(
        _token: str,
        _course_id: str,
        user_email: str,
        *,
        role: str = "student",
    ) -> tuple[bool, str]:
        assert role == "student"
        if user_email == "missing@example.com":
            return False, "Fant ingen bruker med e-post 'missing@example.com'."
        return True, "Bruker lagt til i faget."

    monkeypatch.setattr(teacher_course_page._course_api, "enroll_user", _fake_enroll_user)
    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")
    monkeypatch.setattr(teacher_course_page.gr, "Warning", warnings.append)

    _file_update, _students_text, import_results, _message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert "- Ikke registrert i appen: 1" in import_results
    assert "#### Ikke registrerte e-poster" in import_results
    assert "- missing@example.com" in import_results
    assert warnings == ["1 e-postadresse finnes ikke i systemet. Se importresultatet for detaljer."]


def test_handle_import_students_csv_handles_mixed_results(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-8",
        TOKEN_KEY: "token-8",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text(
        "email\n"
        "added@example.com\n"
        "already@example.com\n"
        "missing@example.com\n"
        "broken@example.com\n",
        encoding="utf-8",
    )

    def _fake_enroll_user(
        _token: str,
        _course_id: str,
        user_email: str,
        *,
        role: str = "student",
    ) -> tuple[bool, str]:
        assert role == "student"
        if user_email == "added@example.com":
            return True, "Bruker lagt til i faget."
        if user_email == "already@example.com":
            return False, "Brukeren er allerede registrert i faget."
        if user_email == "missing@example.com":
            return False, "Fant ingen bruker med e-post 'missing@example.com'."
        return False, "Kunne ikke nå API-serveren: timeout"

    monkeypatch.setattr(teacher_course_page._course_api, "enroll_user", _fake_enroll_user)
    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")
    monkeypatch.setattr(teacher_course_page.gr, "Warning", lambda _message: None)

    _file_update, _students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert "- Importert: 1" in import_results
    assert "- Allerede registrert: 1" in import_results
    assert "- Ikke registrert i appen: 1" in import_results
    assert "- Andre feil: 1" in import_results
    assert "- Rad 3: already@example.com er allerede registrert." in import_results
    assert "- Rad 4: missing@example.com finnes ikke i systemet." in import_results
    assert "- Rad 5: broken@example.com feilet (Kunne ikke nå API-serveren: timeout)." in import_results
    assert message == "Import fullført med delvise feil."


def test_handle_import_students_csv_requires_token() -> None:
    state: dict[str, Any] = {COURSE_ID_KEY: "course-9"}

    file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        "/tmp/students.csv",
    )

    assert file_update.get("value") is None
    assert students_text == "Sessionen er utløpt — logg inn på nytt."
    assert import_results == ""
    assert message == "Sessionen er utløpt — logg inn på nytt."


def test_handle_import_students_csv_requires_course_id() -> None:
    state: dict[str, Any] = {TOKEN_KEY: "token-9"}

    file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        "/tmp/students.csv",
    )

    assert file_update.get("value") is None
    assert students_text == "Ingen studenter ennå."
    assert import_results == ""
    assert message == "Fant ikke faget."


def test_handle_import_students_csv_requires_file(monkeypatch) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-10",
        TOKEN_KEY: "token-10",
    }
    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")

    _file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        None,
    )

    assert students_text == "students"
    assert import_results == ""
    assert message == "Velg en CSV-fil."


def test_handle_import_students_csv_rejects_wrong_extension(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-11",
        TOKEN_KEY: "token-11",
    }
    file_path = tmp_path / "students.txt"
    file_path.write_text("ada@example.com\n", encoding="utf-8")

    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")

    _file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        str(file_path),
    )

    assert students_text == "students"
    assert import_results == ""
    assert message == "Velg en CSV-fil med filendelsen .csv."


def test_handle_import_students_csv_handles_empty_csv(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-12",
        TOKEN_KEY: "token-12",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("email\n\n", encoding="utf-8")

    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")

    _file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert students_text == "students"
    assert "Ingen e-postadresser funnet i CSV-filen." in import_results
    assert message == "CSV-filen inneholder ingen e-postadresser."


def test_handle_import_students_csv_handles_all_invalid_rows(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-13",
        TOKEN_KEY: "token-13",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("email\nnot-an-email\nstill-bad\n", encoding="utf-8")

    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")

    _file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert students_text == "students"
    assert "- Ugyldige rader: 2" in import_results
    assert "Ingen gyldige e-postadresser funnet i CSV-filen." in import_results
    assert message == "Ingen gyldige e-postadresser funnet."


def test_handle_import_students_csv_reports_when_all_enrollments_fail(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-14",
        TOKEN_KEY: "token-14",
    }
    csv_path = tmp_path / "students.csv"
    csv_path.write_text("email\nalready@example.com\nmissing@example.com\n", encoding="utf-8")

    def _fake_enroll_user(
        _token: str,
        _course_id: str,
        user_email: str,
        *,
        role: str = "student",
    ) -> tuple[bool, str]:
        assert role == "student"
        if user_email == "already@example.com":
            return False, "Brukeren er allerede registrert i faget."
        return False, "Fant ingen bruker med e-post 'missing@example.com'."

    monkeypatch.setattr(teacher_course_page._course_api, "enroll_user", _fake_enroll_user)
    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")
    monkeypatch.setattr(teacher_course_page.gr, "Warning", lambda _message: None)

    _file_update, students_text, import_results, message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert students_text == "students"
    assert "- Importert: 0" in import_results
    assert "- Allerede registrert: 1" in import_results
    assert "- Ikke registrert i appen: 1" in import_results
    assert message == "Ingen studenter ble importert."


def test_handle_import_students_csv_limits_detail_lines(monkeypatch, tmp_path: Path) -> None:
    state: dict[str, Any] = {
        COURSE_ID_KEY: "course-15",
        TOKEN_KEY: "token-15",
    }
    csv_path = tmp_path / "students.csv"
    invalid_rows = "".join(f"bad-{index}\n" for index in range(12))
    csv_path.write_text(f"email\n{invalid_rows}", encoding="utf-8")

    monkeypatch.setattr(teacher_course_page, "teacher_course_students_text", lambda _state: "students")

    _file_update, _students_text, import_results, _message = teacher_course_page.handle_import_students_csv(
        state,
        str(csv_path),
    )

    assert "- Og 2 til." in import_results


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
