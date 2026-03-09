"""Teacher course page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.router import ROUTE_CHAT
from src.ui.state import COURSE_ID_KEY, COURSE_NAME_KEY, auth_token, with_route


@dataclass(slots=True)
class TeacherCoursePageComponents:
    group: gr.Group
    back_button: gr.Button
    course_title: gr.Markdown
    students_list: gr.Markdown
    view_as_student_button: gr.Button
    add_student_username: gr.Textbox
    add_student_button: gr.Button
    upload_files: gr.File
    upload_button: gr.Button
    materials_list: gr.Radio
    delete_material_button: gr.Button
    refresh_materials_button: gr.Button
    start_ingestion_button: gr.Button
    refresh_ingestion_button: gr.Button
    ingestion_status: gr.Markdown
    status_text: gr.Markdown


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def _material_label(material: dict[str, Any]) -> str:
    filename = str(material.get("original_filename") or "ukjent")
    size_bytes = int(material.get("size_bytes") or 0)
    size_kb = max(1, size_bytes // 1024) if size_bytes > 0 else 0
    return f"{filename} ({size_kb} KB)"


def teacher_course_material_choices_update(state: dict[str, Any]) -> Any:
    course_id = _current_course_id(state)
    if not course_id:
        return gr.update(choices=[], value=None)
    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=None)

    materials, _err = _course_api.list_materials(token, course_id)
    choices = [
        (_material_label(item), str(item["id"]))
        for item in materials
        if isinstance(item, dict) and item.get("id")
    ]
    return gr.update(choices=choices, value=None)


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

        gr.Markdown("## Kursmateriale")
        upload_files = gr.File(
            label="Velg filer",
            file_count="multiple",
            type="filepath",
        )
        upload_button = gr.Button("Last opp filer", variant="primary")
        materials_list = gr.Radio(choices=[], value=None, label="Opplastet materiale")
        with gr.Row():
            delete_material_button = gr.Button("Slett valgt materiale")
            refresh_materials_button = gr.Button("Oppdater materialliste")

        gr.Markdown("## Ingestion")
        with gr.Row():
            start_ingestion_button = gr.Button("Start ingestion", variant="primary")
            refresh_ingestion_button = gr.Button("Oppdater status")
        ingestion_status = gr.Markdown("Ingen ingestion-jobber ennå.")

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
        upload_files=upload_files,
        upload_button=upload_button,
        materials_list=materials_list,
        delete_material_button=delete_material_button,
        refresh_materials_button=refresh_materials_button,
        start_ingestion_button=start_ingestion_button,
        refresh_ingestion_button=refresh_ingestion_button,
        ingestion_status=ingestion_status,
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

    enrollments, err = _course_api.list_enrollments(token, course_id)
    if err:
        return err
    if not enrollments:
        return "Ingen studenter ennå."

    lines: list[str] = []
    for item in enrollments:
        user = item.get("user", {}) if isinstance(item, dict) else {}
        role = str(item.get("role") or "student")
        role_label = "Lærer" if role == "teacher" else "Student"
        email = str(user.get("email") or "-")
        first = str(user.get("first_name") or "").strip()
        last = str(user.get("last_name") or "").strip()
        name = " ".join(part for part in (first, last) if part) or email
        lines.append(f"- {role_label}: {name} ({email})")
    return "\n".join(lines)


def teacher_course_ingestion_status_text(state: dict[str, Any]) -> str:
    course_id = _current_course_id(state)
    if not course_id:
        return "Ingen ingestion-jobber ennå."

    token = auth_token(state)
    if not token:
        return "Sessionen er utløpt — logg inn på nytt."

    jobs, err = _course_api.list_ingestions(token, course_id)
    if err:
        return err
    if not jobs:
        return "Ingen ingestion-jobber ennå."

    latest = jobs[0]
    status = str(latest.get("status") or "ukjent")
    created = str(latest.get("created_at") or "")[:19]
    finished = str(latest.get("finished_at") or "")[:19]
    error = str(latest.get("error_message") or "").strip()

    text = f"Siste jobb: {status} (startet: {created or '-'})"
    if finished:
        text += f"\nFerdig: {finished}"
    if error:
        text += f"\nFeil: {error}"
    return text


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


def handle_upload_materials(
    state: dict[str, Any],
    file_paths: str | list[str] | None,
) -> tuple[Any, Any, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return gr.update(value=None), teacher_course_material_choices_update(state), "Fant ikke faget."

    token = auth_token(state)
    if not token:
        return gr.update(value=None), teacher_course_material_choices_update(state), "Sessionen er utløpt — logg inn på nytt."

    if isinstance(file_paths, str):
        files = [file_paths]
    elif isinstance(file_paths, list):
        files = [str(item) for item in file_paths if item]
    else:
        files = []

    if not files:
        return gr.update(value=None), teacher_course_material_choices_update(state), "Velg minst én fil."

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
    return gr.update(value=None), teacher_course_material_choices_update(state), status_message


def handle_delete_material(state: dict[str, Any], material_id: str | None) -> tuple[Any, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return teacher_course_material_choices_update(state), "Fant ikke faget."

    token = auth_token(state)
    if not token:
        return teacher_course_material_choices_update(state), "Sessionen er utløpt — logg inn på nytt."

    selected_id = str(material_id or "").strip()
    if not selected_id:
        return teacher_course_material_choices_update(state), "Velg materiale som skal slettes."

    success, message = _course_api.delete_material(token, course_id, selected_id)
    return teacher_course_material_choices_update(state), message if success else message


def handle_start_ingestion(state: dict[str, Any]) -> tuple[str, str]:
    course_id = _current_course_id(state)
    if not course_id:
        return teacher_course_ingestion_status_text(state), "Fant ikke faget."

    token = auth_token(state)
    if not token:
        return teacher_course_ingestion_status_text(state), "Sessionen er utløpt — logg inn på nytt."

    success, message, _job = _course_api.start_ingestion(token, course_id)
    return teacher_course_ingestion_status_text(state), message if success else message


def handle_refresh_ingestion(state: dict[str, Any]) -> tuple[str, str]:
    return teacher_course_ingestion_status_text(state), "Ingestion-status oppdatert."


def handle_view_as_student(state: dict[str, Any]) -> tuple[dict[str, Any], str]:
    course_id = _current_course_id(state)
    if not course_id:
        return state, "Fant ikke faget."
    return with_route(state, ROUTE_CHAT), ""
