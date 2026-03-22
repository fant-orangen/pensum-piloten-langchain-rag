"""Teacher course student tab UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.course_service as _course_api
from src.ui.state import COURSE_ID_KEY, ENROLLMENT_PREVIEW_ID_KEY, auth_token


@dataclass(slots=True)
class TeacherCourseStudentsTabComponents:
    group: gr.Group
    students_list: gr.Markdown
    add_student_username: gr.Textbox
    add_student_button: gr.Button
    import_students_file: gr.File
    import_students_button: gr.Button
    confirm_import_button: gr.Button
    import_results: gr.Markdown
    status_text: gr.Markdown


def _current_course_id(state: dict[str, Any]) -> str:
    return str(state.get(COURSE_ID_KEY) or "").strip()


def build_teacher_course_students_tab() -> TeacherCourseStudentsTabComponents:
    with gr.Group() as group:
        students_list = gr.Markdown("Ingen studenter ennå.")
        with gr.Group():
            gr.Markdown("### Legg til én student")
            add_student_username = gr.Textbox(
                label="Studentens e-post",
                placeholder="student@example.com",
            )
            add_student_button = gr.Button("Legg til student", variant="primary")
        with gr.Group():
            gr.Markdown("### Importer fra CSV")
            gr.Markdown(
                "Last opp en CSV-fil med kolonnene: **e-post**, fornavn (valgfritt), etternavn (valgfritt). "
                "Studenter uten eksisterende konto får opprettet konto automatisk ved bekreftelse."
            )
            import_students_file = gr.File(
                label="CSV med studenter",
                file_count="single",
                file_types=[".csv"],
                type="filepath",
            )
            import_students_button = gr.Button("Forhåndsvis import", variant="primary")
            confirm_import_button = gr.Button("Bekreft import", variant="primary", visible=False)
            import_results = gr.Markdown()
        status_text = gr.Markdown()

    return TeacherCourseStudentsTabComponents(
        group=group,
        students_list=students_list,
        add_student_username=add_student_username,
        add_student_button=add_student_button,
        import_students_file=import_students_file,
        import_students_button=import_students_button,
        confirm_import_button=confirm_import_button,
        import_results=import_results,
        status_text=status_text,
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
        lines.append(f"- {name} ({email})")
    return "\n".join(lines)


def teacher_course_student_choices_update(_state: dict[str, Any], *, selected_username: str | None = None) -> Any:
    return gr.update(value=selected_username or "")


def teacher_course_student_import_file_update(_state: dict[str, Any]) -> Any:
    return gr.update(value=None)


def teacher_course_student_import_results_update(_state: dict[str, Any]) -> str:
    return ""


def teacher_course_student_status_update(_state: dict[str, Any]) -> str:
    return ""


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
    return (
        gr.update(value="" if success else email),
        teacher_course_students_text(state),
        message,
    )


def handle_import_students_csv(
    state: dict[str, Any],
    csv_path: str | None,
) -> tuple[dict[str, Any], Any, Any, str, str]:
    """Upload CSV to the preview endpoint and show results without enrolling anyone yet.

    Returns: (state, confirm_button_update, import_results, status_text)
    """
    course_id = _current_course_id(state)
    token = auth_token(state)

    if not course_id or not token:
        return state, gr.update(visible=False), "", "Sessionen er utløpt — logg inn på nytt."

    if not isinstance(csv_path, str) or not csv_path.strip().lower().endswith(".csv"):
        return state, gr.update(visible=False), "", "Velg en CSV-fil."

    success, error_msg, data = _course_api.preview_enrollment_import(token, course_id, csv_path.strip())
    if not success or data is None:
        return state, gr.update(visible=False), "", error_msg

    enrollable = data.get("enrollable_emails") or []
    missing = data.get("missing_candidates") or []
    already = data.get("already_enrolled_emails") or []
    invalid = data.get("invalid_emails") or []

    lines = [f"**{len(enrollable)} eksisterende student(er) vil bli innmeldt.**"]
    if missing:
        lines.append(f"**{len(missing)} student(er) finnes ikke i systemet — nye kontoer vil bli opprettet:**")
        for c in missing:
            email = c.get("email", "")
            first = str(c.get("first_name") or "").strip()
            last = str(c.get("last_name") or "").strip()
            name = " ".join(p for p in (first, last) if p)
            lines.append(f"- {name} ({email})" if name else f"- {email}")
    if already:
        lines.append(f"{len(already)} er allerede innmeldt og hoppes over.")
    if invalid:
        lines.append(f"{len(invalid)} ugyldige rader ignorert.")

    next_state = dict(state)
    next_state[ENROLLMENT_PREVIEW_ID_KEY] = data.get("preview_id")

    return (
        next_state,
        gr.update(visible=True),
        "\n".join(lines),
        "Gjennomgå og trykk Bekreft for å fullføre importen.",
    )


def handle_confirm_enrollment(
    state: dict[str, Any],
) -> tuple[dict[str, Any], Any, str, str, str]:
    """Confirm the staged import: create missing accounts and enroll everyone.

    Returns: (state, confirm_button_update, students_list, import_results, status_text)
    """
    course_id = _current_course_id(state)
    token = auth_token(state)
    preview_id = state.get(ENROLLMENT_PREVIEW_ID_KEY)

    next_state = dict(state)
    next_state[ENROLLMENT_PREVIEW_ID_KEY] = None

    if not course_id or not token or not preview_id:
        return next_state, gr.update(visible=False), teacher_course_students_text(next_state), "", "Ingen aktiv forhåndsvisning."

    success, error_msg, data = _course_api.confirm_enrollment_import(token, course_id, str(preview_id))
    if not success or data is None:
        return next_state, gr.update(visible=False), teacher_course_students_text(next_state), "", error_msg

    enrolled = data.get("enrolled_emails") or []
    created = data.get("created_emails") or []
    status = f"Import fullført — {len(enrolled)} student(er) innmeldt" + (f", {len(created)} nye kontoer opprettet." if created else ".")

    return (
        next_state,
        gr.update(visible=False),
        teacher_course_students_text(next_state),
        "",
        status,
    )
