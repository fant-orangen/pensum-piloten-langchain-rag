"""Teacher course materials tab UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.state import COURSE_ID_KEY, auth_token


@dataclass(slots=True)
class TeacherCourseMaterialsTabComponents:
    group: gr.Group
    upload_files: gr.File
    upload_button: gr.Button
    materials_list: gr.CheckboxGroup
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


def build_teacher_course_materials_tab() -> TeacherCourseMaterialsTabComponents:
    with gr.Group() as group:
        with gr.Group():
            gr.Markdown("### Kildemateriale")
            upload_files = gr.File(
                label="Velg filer",
                file_count="multiple",
                type="filepath",
            )
            upload_button = gr.Button("Last opp filer", variant="primary")
            gr.Markdown("Velg ett eller flere materialer under for sletting.")
            materials_list = gr.CheckboxGroup(
                choices=[],
                value=[],
                label="Kursmateriell",
            )
            with gr.Row():
                delete_material_button = gr.Button("Slett valgte materialer", variant="secondary")
                refresh_materials_button = gr.Button("Oppdater materialliste", variant="secondary")

        with gr.Group():
            gr.Markdown("### Ingestering")
            gr.Markdown("Ingestering starter for alle stagede endringer i kurset.")
            with gr.Row():
                start_ingestion_button = gr.Button("Start ingestering", variant="primary")
                refresh_ingestion_button = gr.Button("Oppdater status", variant="secondary")
            ingestion_status = gr.Markdown("Ingen ingesteringstatus ennå.")
        status_text = gr.Markdown()

    return TeacherCourseMaterialsTabComponents(
        group=group,
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


def teacher_course_material_status_update(_state: dict[str, Any]) -> str:
    return ""


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
    zip_messages: list[str] = []
    for path in files:
        if path.lower().endswith(".zip"):
            success, message, _data = _course_api.upload_zip_material(token, course_id, path)
            if success:
                zip_messages.append(message)
            else:
                errors.append(message)
        else:
            success, message, _data = _course_api.upload_material(token, course_id, path)
            if success:
                uploaded += 1
            else:
                errors.append(message)

    parts: list[str] = []
    if uploaded:
        parts.append(f"Lastet opp {uploaded} fil(er).")
    parts.extend(zip_messages)
    status_message = " ".join(parts) if parts else ""
    if errors:
        status_message += (" " if status_message else "") + f"Feil: {' | '.join(errors)}"
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
