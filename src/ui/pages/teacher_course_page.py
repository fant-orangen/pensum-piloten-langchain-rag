"""Teacher course page UI and handlers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gradio as gr
from email_validator import EmailNotValidError, validate_email

import src.ui.services.course_service as _course_api
from src.ui.router import ROUTE_CHAT
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token, with_route

MAX_COURSE_INSTRUCTIONS_CHARS = 3000
CSV_HEADER_LABELS = {"email", "e-mail", "epost", "e-post", "user_email"}
MAX_IMPORT_RESULT_DETAIL_LINES = 10


@dataclass(slots=True)
class TeacherCoursePageComponents:
    group: gr.Group
    back_button: gr.Button
    course_title: gr.Markdown
    students_list: gr.Markdown
    view_as_student_button: gr.Button
    add_student_username: gr.Textbox
    add_student_button: gr.Button
    import_students_file: gr.File
    import_students_button: gr.Button
    import_results: gr.Markdown
    upload_files: gr.File
    upload_button: gr.Button
    materials_list: gr.CheckboxGroup
    delete_material_button: gr.Button
    refresh_materials_button: gr.Button
    start_ingestion_button: gr.Button
    refresh_ingestion_button: gr.Button
    ingestion_status: gr.Markdown
    course_instructions_input: gr.Textbox
    course_instructions_counter: gr.Markdown
    save_course_instructions_button: gr.Button
    status_text: gr.Markdown


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def _material_label(material: dict[str, Any]) -> str:
    filename = str(material.get("original_filename") or "ukjent")
    size_bytes = int(material.get("size_bytes") or 0)
    status = str(material.get("status") or "").strip().lower()
    status_label = {
        "pending_add": "Venter på ingestering",
        "active": "Ingestert",
        "pending_remove": "Markert for sletting",
    }.get(status, "Ukjent status")
    if size_bytes > 0:
        size_kb = max(1, size_bytes // 1024)
        return f"{filename} ({size_kb} KB) - {status_label}"
    return f"{filename} - {status_label}"


def teacher_course_material_choices_update(state: dict[str, Any]) -> Any:
    course_id = _current_course_id(state)
    if not course_id:
        return gr.update(choices=[], value=[])
    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=[])

    materials, _err = _course_api.list_materials(token, course_id)
    choices = [
        (_material_label(item), str(item["id"]))
        for item in materials
        if isinstance(item, dict) and item.get("id")
    ]
    return gr.update(choices=choices, value=[])


def _course_instructions_counter_text(instructions_text: str | None) -> str:
    instruction_length = len(str(instructions_text or ""))
    return f"Tegn brukt: {instruction_length}/{MAX_COURSE_INSTRUCTIONS_CHARS}"


def teacher_course_instructions_input_update(_state: dict[str, Any]) -> Any:
    # Frontend is currently write-only for this field; do not prefill saved value yet.
    return gr.update(value="")


def teacher_course_instructions_counter_update(_state: dict[str, Any]) -> str:
    return _course_instructions_counter_text("")


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
) -> str:
    lines = [
        "### Importresultat",
        f"- Importert: {imported_count}",
        f"- Allerede registrert: {already_enrolled_count}",
        f"- Ikke registrert i appen: {missing_user_count}",
        f"- Ugyldige rader: {invalid_row_count}",
        f"- Andre feil: {other_error_count}",
    ]
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


def handle_course_instructions_input(instructions_text: str | None) -> str:
    return _course_instructions_counter_text(instructions_text)


def build_teacher_course_page(*, visible: bool) -> TeacherCoursePageComponents:
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Fag")
        course_title = gr.Markdown("Fag: -")
        view_as_student_button = gr.Button("Se som student", variant="secondary")

        gr.Markdown("## Studenter")
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

        gr.Markdown("## Kursmateriale")
        upload_files = gr.File(
            label="Velg filer",
            file_count="multiple",
            type="filepath",
        )
        upload_button = gr.Button("Last opp filer", variant="primary")
        gr.Markdown("Velg ett eller flere materialer under for sletting.")
        gr.Markdown("Ingestering starter for alle stagede endringer i kurset.")
        materials_list = gr.CheckboxGroup(
            choices=[],
            value=[],
            label="Kursmateriell",
        )
        with gr.Row():
            delete_material_button = gr.Button("Slett valgte materialer")
            refresh_materials_button = gr.Button("Oppdater materialliste")

        gr.Markdown("## Ingestering (oppsummering)")
        with gr.Row():
            start_ingestion_button = gr.Button("Start ingestering", variant="primary")
            refresh_ingestion_button = gr.Button("Oppdater status")
        ingestion_status = gr.Markdown("Ingen ingesteringstatus ennå.")

        gr.Markdown("## Kursinstruksjoner for modellen")
        gr.Markdown(
            "Legg til egne instruksjoner som blir lagt til systemprompten for dette faget. "
            "Det er foreløpig ikke mulig å hente eksisterende lagrede instruksjoner."
        )
        course_instructions_input = gr.Textbox(
            label="Instruksjoner (maks 3000 tegn)",
            placeholder=(
                "Eksempel: Prioriter pensumbegreper fra uke 1–5, bruk norske fagtermer, "
                "og gi korte stegvise hint før fasitsvar."
            ),
            lines=8,
            max_lines=12,
        )
        course_instructions_counter = gr.Markdown(_course_instructions_counter_text(""))
        save_course_instructions_button = gr.Button(
            "Lagre instruksjoner",
            variant="primary",
        )

        status_text = gr.Markdown()
        back_button = gr.Button("Tilbake")

    return TeacherCoursePageComponents(
        group=group,
        back_button=back_button,
        course_title=course_title,
        students_list=students_list,
        view_as_student_button=view_as_student_button,
        add_student_username=add_student_username,
        add_student_button=add_student_button,
        import_students_file=import_students_file,
        import_students_button=import_students_button,
        import_results=import_results,
        upload_files=upload_files,
        upload_button=upload_button,
        materials_list=materials_list,
        delete_material_button=delete_material_button,
        refresh_materials_button=refresh_materials_button,
        start_ingestion_button=start_ingestion_button,
        refresh_ingestion_button=refresh_ingestion_button,
        ingestion_status=ingestion_status,
        course_instructions_input=course_instructions_input,
        course_instructions_counter=course_instructions_counter,
        save_course_instructions_button=save_course_instructions_button,
        status_text=status_text,
    )


def teacher_course_title_text(state: dict[str, Any]) -> str:
    course_name = str(state.get(COURSE_NAME_KEY) or "").strip()
    if not course_name:
        course_id = _current_course_id(state)
        if not course_id:
            return "Fag: -"
        token = auth_token(state)
        if not token:
            return "Fag: -"
        courses, _err = _course_api.list_courses(token)
        course = next(
            (c for c in courses if isinstance(c, dict) and c.get("id") == course_id),
            None,
        )
        if course is None:
            return "Fag: -"
        return f"Fag: {course.get('name', '-')}"
    return f"Fag: {course_name}"


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


def teacher_course_ingestion_status_text(state: dict[str, Any]) -> str:
    course_id = _current_course_id(state)
    if not course_id:
        return "Velg et fag for å se ingesteringstatus."

    token = auth_token(state)
    if not token:
        return "Sessionen er utløpt — logg inn på nytt."

    jobs, err = _course_api.list_ingestions(token, course_id)
    if err:
        return err
    if not jobs:
        return "Ingen ingesteringstatus tilgjengelig."

    latest = jobs[0]
    status = str(latest.get("status") or "ukjent").strip().lower()
    status_label = {
        "idle": "Klar",
        "queued": "Venter i kø",
        "building": "Bygger indeks",
        "failed": "Feilet",
    }.get(status, status or "ukjent")
    pending_additions = int(latest.get("pending_additions") or 0)
    pending_removals = int(latest.get("pending_removals") or 0)
    index_version = int(latest.get("index_version") or 0)
    rebuild_error = str(latest.get("rebuild_error") or "").strip()

    lines = [
        f"Status: {status_label}",
        f"Venter på ingestering: {pending_additions}",
        f"Markert for sletting: {pending_removals}",
        f"Aktiv indeksversjon: {index_version}",
    ]
    if rebuild_error:
        lines.append(f"Siste feil: {rebuild_error}")
    return "\n".join(lines)


def teacher_course_student_choices_update(state: dict[str, Any], *, selected_username: str | None = None) -> Any:
    return gr.update(value=selected_username or "")


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

    valid_emails, invalid_rows = _parse_student_import_csv(csv_path)
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
        gr.Warning(
            f"{missing_user_count} e-postadresser finnes ikke i systemet. "
            "Se importresultatet for detaljer."
        )
    return (
        teacher_course_student_import_file_update(state),
        teacher_course_students_text(state),
        import_results,
        "CSV-import fullført.",
    )


def handle_upload_materials(
    state: dict[str, Any],
    file_paths: str | list[str] | None,
) -> tuple[Any, Any, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return (
            gr.update(value=None),
            teacher_course_material_choices_update(state),
            "Fant ikke faget.",
        )

    token = auth_token(state)
    if not token:
        return (
            gr.update(value=None),
            teacher_course_material_choices_update(state),
            "Sessionen er utløpt — logg inn på nytt.",
        )

    if isinstance(file_paths, str):
        files = [file_paths]
    elif isinstance(file_paths, list):
        files = [str(item) for item in file_paths if item]
    else:
        files = []

    if not files:
        return (
            gr.update(value=None),
            teacher_course_material_choices_update(state),
            "Velg minst én fil.",
        )

    uploaded = 0
    errors: list[str] = []
    for path in files:
        success, message, _data = _course_api.upload_material(token, course_id, path)
        if success:
            uploaded += 1
        else:
            errors.append(message)

    status_message = f"Lastet opp {uploaded} fil(er)."
    if errors:
        status_message += f" Feil: {' | '.join(errors)}"
    return (
        gr.update(value=None),
        teacher_course_material_choices_update(state),
        status_message,
    )


def handle_delete_material(
    state: dict[str, Any],
    material_ids: list[str] | None,
) -> tuple[Any, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return (
            teacher_course_material_choices_update(state),
            "Fant ikke faget.",
        )

    token = auth_token(state)
    if not token:
        return (
            teacher_course_material_choices_update(state),
            "Sessionen er utløpt — logg inn på nytt.",
        )

    selected_ids = [item.strip() for item in (material_ids or []) if item and item.strip()]
    if not selected_ids:
        return (
            teacher_course_material_choices_update(state),
            "Velg minst ett materiale som skal slettes.",
        )

    deleted = 0
    errors: list[str] = []
    for selected_id in selected_ids:
        success, message = _course_api.delete_material(token, course_id, selected_id)
        if success:
            deleted += 1
        else:
            errors.append(message)

    status_message = f"Slettet {deleted} materiale(r)."
    if errors:
        status_message += f" Feil: {' | '.join(errors)}"
    return (
        teacher_course_material_choices_update(state),
        status_message,
    )


def handle_start_ingestion(
    state: dict[str, Any],
    _selected_material_ids: list[str] | None,
) -> tuple[Any, str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return gr.update(value=[]), teacher_course_ingestion_status_text(state), "Fant ikke faget."

    token = auth_token(state)
    if not token:
        return (
            gr.update(value=[]),
            teacher_course_ingestion_status_text(state),
            "Sessionen er utløpt — logg inn på nytt.",
        )

    success, message, _job = _course_api.start_ingestion(token, course_id)
    return gr.update(value=[]), teacher_course_ingestion_status_text(state), message if success else message


def handle_refresh_ingestion(state: dict[str, Any]) -> tuple[str, str]:
    return teacher_course_ingestion_status_text(state), "Ingestion-status oppdatert."


def handle_save_course_instructions(
    state: dict[str, Any],
    instructions_text: str | None,
) -> tuple[Any, str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        counter_text = _course_instructions_counter_text(instructions_text)
        return gr.update(value=instructions_text or ""), counter_text, "Fant ikke faget."

    token = auth_token(state)
    if not token:
        counter_text = _course_instructions_counter_text(instructions_text)
        return (
            gr.update(value=instructions_text or ""),
            counter_text,
            "Sessionen er utløpt — logg inn på nytt.",
        )

    raw_instructions = str(instructions_text or "")
    if len(raw_instructions) > MAX_COURSE_INSTRUCTIONS_CHARS:
        counter_text = _course_instructions_counter_text(raw_instructions)
        return (
            gr.update(value=raw_instructions),
            counter_text,
            f"Instruksjonene er for lange. Maks {MAX_COURSE_INSTRUCTIONS_CHARS} tegn.",
        )

    cleaned_instructions = raw_instructions.strip()
    payload_instructions = cleaned_instructions or None

    success, message, _course = _course_api.update_course_instructions(
        token,
        course_id,
        payload_instructions,
    )
    # Keep the visible input normalized after successful save.
    next_input_value = cleaned_instructions if success else raw_instructions
    return (
        gr.update(value=next_input_value),
        _course_instructions_counter_text(next_input_value),
        message,
    )


def handle_view_as_student(state: dict[str, Any]) -> tuple[dict[str, Any], str]:
    course_id = _current_course_id(state)
    if not course_id:
        return state, "Fant ikke faget."
    return with_route(state, ROUTE_CHAT), ""
