"""Teacher course student tab UI and handlers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gradio as gr
from email_validator import EmailNotValidError, validate_email

import src.ui.services.course_service as _course_api
from src.ui.state import COURSE_ID_KEY, auth_token

CSV_HEADER_LABELS = {"email", "e-mail", "epost", "e-post", "user_email"}
MAX_IMPORT_RESULT_DETAIL_LINES = 10


@dataclass(slots=True)
class TeacherCourseStudentsTabComponents:
    group: gr.Group
    students_list: gr.Markdown
    add_student_username: gr.Textbox
    add_student_button: gr.Button
    import_students_file: gr.File
    import_students_button: gr.Button
    import_results: gr.Markdown


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def build_teacher_course_students_tab() -> TeacherCourseStudentsTabComponents:
    with gr.Group() as group:
        students_list = gr.Markdown("Ingen studenter ennå.")
        add_student_username = gr.Textbox(
            label="Studentens e-post",
            placeholder="student@example.com",
        )
        add_student_button = gr.Button("Legg til student", variant="primary")
        gr.Markdown("### Importer studenter fra CSV")
        gr.Markdown(
            "Last opp en CSV-fil med én e-postadresse per rad. "
            "Valgfri overskriftsrad støttes, og tomme rader ignoreres."
        )
        import_students_file = gr.File(
            label="CSV med student-e-poster",
            file_count="single",
            file_types=[".csv"],
            type="filepath",
        )
        import_students_button = gr.Button("Importer studenter", variant="secondary")
        import_results = gr.Markdown()

    return TeacherCourseStudentsTabComponents(
        group=group,
        students_list=students_list,
        add_student_username=add_student_username,
        add_student_button=add_student_button,
        import_students_file=import_students_file,
        import_students_button=import_students_button,
        import_results=import_results,
    )


def teacher_course_students_text(state: dict[str, Any]) -> str:
    course_id = _current_course_id(state)
    if not course_id:
        return "Ingen studenter ennå."

    token = auth_token(state)
    if not token:
        return "Sessionen er utløpt — logg inn på nytt."

    students, err = _course_api.list_course_students(token, course_id)
    if err:
        return err
    if not students:
        return "Ingen studenter ennå."

    lines: list[str] = []
    for item in students:
        email = str(item.get("email") or "-")
        first = str(item.get("first_name") or "").strip()
        last = str(item.get("last_name") or "").strip()
        name = " ".join(part for part in (first, last) if part) or email
        lines.append(f"- Student: {name} ({email})")
    return "\n".join(lines)


def teacher_course_student_choices_update(_state: dict[str, Any], *, selected_username: str | None = None) -> Any:
    return gr.update(value=selected_username or "")


def teacher_course_student_import_file_update(_state: dict[str, Any]) -> Any:
    return gr.update(value=None)


def teacher_course_student_import_results_update(_state: dict[str, Any]) -> str:
    return ""


def _is_csv_header(value: str) -> bool:
    return value.strip().lower() in CSV_HEADER_LABELS


def _parse_student_import_csv(csv_path: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    valid_emails: list[tuple[int, str]] = []
    invalid_rows: list[tuple[int, str]] = []
    seen_emails: set[str] = set()
    first_non_empty_row_seen = False

    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row_number, row in enumerate(reader, start=1):
            if not row:
                continue
            first_cell = str(row[0]).strip()
            if not first_cell:
                continue
            if not first_non_empty_row_seen:
                first_non_empty_row_seen = True
                if _is_csv_header(first_cell):
                    continue
            try:
                normalized_email = validate_email(
                    first_cell,
                    check_deliverability=False,
                ).normalized
            except EmailNotValidError:
                invalid_rows.append((row_number, first_cell))
                continue
            dedupe_key = normalized_email.casefold()
            if dedupe_key in seen_emails:
                continue
            seen_emails.add(dedupe_key)
            valid_emails.append((row_number, normalized_email))

    return valid_emails, invalid_rows


def _classify_enrollment_error(message: str) -> str:
    if message == "Brukeren er allerede registrert i faget.":
        return "already_enrolled"
    if message.startswith("Fant ingen bruker med e-post "):
        return "missing_user"
    return "other_error"


def _build_import_results_text(
    *,
    imported_count: int,
    already_enrolled_count: int,
    missing_user_count: int,
    invalid_row_count: int,
    other_error_count: int,
    missing_emails: list[str],
    detail_lines: list[str],
    note: str | None = None,
) -> str:
    lines = [
        "### Importresultat",
        f"- Importert: {imported_count}",
        f"- Allerede registrert: {already_enrolled_count}",
        f"- Ikke registrert i appen: {missing_user_count}",
        f"- Ugyldige rader: {invalid_row_count}",
        f"- Andre feil: {other_error_count}",
    ]
    if note:
        lines.append("")
        lines.append(note)
    if missing_emails:
        lines.append("")
        lines.append("#### Ikke registrerte e-poster")
        lines.extend(f"- {email}" for email in missing_emails)
    if detail_lines:
        lines.append("")
        lines.append("#### Detaljer")
        lines.extend(detail_lines[:MAX_IMPORT_RESULT_DETAIL_LINES])
        extra_count = len(detail_lines) - MAX_IMPORT_RESULT_DETAIL_LINES
        if extra_count > 0:
            lines.append(f"- Og {extra_count} til.")
    return "\n".join(lines)


def _build_import_status_message(
    *,
    imported_count: int,
    already_enrolled_count: int,
    missing_user_count: int,
    invalid_row_count: int,
    other_error_count: int,
) -> str:
    issue_count = (
        already_enrolled_count
        + missing_user_count
        + invalid_row_count
        + other_error_count
    )
    if imported_count > 0 and issue_count == 0:
        return "Import fullført."
    if imported_count > 0:
        return "Import fullført med delvise feil."
    return "Ingen studenter ble importert."


def handle_add_student(state: dict[str, Any], student_email: str | None) -> tuple[Any, str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return gr.update(value=""), teacher_course_students_text(state), "Fant ikke faget."

    token = auth_token(state)
    if not token:
        return gr.update(value=""), teacher_course_students_text(state), "Sessionen er utløpt — logg inn på nytt."

    email = (student_email or "").strip()
    if not email:
        return gr.update(value=""), teacher_course_students_text(state), "Fyll ut e-postadressen."

    success, message = _course_api.enroll_user(token, course_id, email, role="student")
    next_input_value = "" if success else email
    return (
        gr.update(value=next_input_value),
        teacher_course_students_text(state),
        message,
    )


def handle_import_students_csv(
    state: dict[str, Any],
    csv_path: str | None,
) -> tuple[Any, str, str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            teacher_course_student_import_results_update(state),
            "Fant ikke faget.",
        )

    token = auth_token(state)
    if not token:
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            teacher_course_student_import_results_update(state),
            "Sessionen er utløpt — logg inn på nytt.",
        )

    if not isinstance(csv_path, str) or not csv_path.strip():
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            teacher_course_student_import_results_update(state),
            "Velg en CSV-fil.",
        )

    cleaned_csv_path = csv_path.strip()
    csv_file_path = Path(cleaned_csv_path)
    if csv_file_path.suffix.lower() != ".csv":
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            teacher_course_student_import_results_update(state),
            "Velg en CSV-fil med filendelsen .csv.",
        )

    try:
        valid_emails, invalid_rows = _parse_student_import_csv(cleaned_csv_path)
    except (OSError, UnicodeDecodeError, csv.Error):
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            teacher_course_student_import_results_update(state),
            "Kunne ikke lese CSV-filen.",
        )

    if not valid_emails and not invalid_rows:
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            _build_import_results_text(
                imported_count=0,
                already_enrolled_count=0,
                missing_user_count=0,
                invalid_row_count=0,
                other_error_count=0,
                missing_emails=[],
                detail_lines=[],
                note="Ingen e-postadresser funnet i CSV-filen.",
            ),
            "CSV-filen inneholder ingen e-postadresser.",
        )

    if not valid_emails and invalid_rows:
        return (
            teacher_course_student_import_file_update(state),
            teacher_course_students_text(state),
            _build_import_results_text(
                imported_count=0,
                already_enrolled_count=0,
                missing_user_count=0,
                invalid_row_count=len(invalid_rows),
                other_error_count=0,
                missing_emails=[],
                detail_lines=[
                    f"- Rad {row_number}: ugyldig e-post '{email}'."
                    for row_number, email in invalid_rows
                ],
                note="Ingen gyldige e-postadresser funnet i CSV-filen.",
            ),
            "Ingen gyldige e-postadresser funnet.",
        )

    imported_count = 0
    already_enrolled_count = 0
    missing_user_count = 0
    other_error_count = 0
    missing_emails: list[str] = []
    detail_lines = [f"- Rad {row_number}: ugyldig e-post '{email}'." for row_number, email in invalid_rows]

    for row_number, email in valid_emails:
        success, message = _course_api.enroll_user(token, course_id, email, role="student")
        if success:
            imported_count += 1
            continue
        error_type = _classify_enrollment_error(message)
        if error_type == "already_enrolled":
            already_enrolled_count += 1
            detail_lines.append(f"- Rad {row_number}: {email} er allerede registrert.")
        elif error_type == "missing_user":
            missing_user_count += 1
            missing_emails.append(email)
            detail_lines.append(f"- Rad {row_number}: {email} finnes ikke i systemet.")
        else:
            other_error_count += 1
            detail_lines.append(f"- Rad {row_number}: {email} feilet ({message}).")

    import_results = _build_import_results_text(
        imported_count=imported_count,
        already_enrolled_count=already_enrolled_count,
        missing_user_count=missing_user_count,
        invalid_row_count=len(invalid_rows),
        other_error_count=other_error_count,
        missing_emails=missing_emails,
        detail_lines=detail_lines,
    )
    if missing_user_count > 0:
        missing_label = "e-postadresse" if missing_user_count == 1 else "e-postadresser"
        gr.Warning(
            f"{missing_user_count} {missing_label} finnes ikke i systemet. "
            "Se importresultatet for detaljer."
        )
    return (
        teacher_course_student_import_file_update(state),
        teacher_course_students_text(state),
        import_results,
        _build_import_status_message(
            imported_count=imported_count,
            already_enrolled_count=already_enrolled_count,
            missing_user_count=missing_user_count,
            invalid_row_count=len(invalid_rows),
            other_error_count=other_error_count,
        ),
    )
