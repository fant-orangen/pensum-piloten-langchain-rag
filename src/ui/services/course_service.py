"""Course service — wraps /courses/* API endpoints."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from src.ui.services.api_client import (
    ApiError,
    ApiUnauthorizedError,
    delete,
    get,
    patch,
    post,
    post_multipart,
)


def list_courses(token: str) -> tuple[list[dict[str, Any]], str]:
    """Fetch all courses the authenticated user is enrolled in.

    Returns:
        (courses, error_message)

        On success, courses is a list of dicts with keys:
            id, name, code, rag_mode
        On failure, courses is empty and error_message is non-empty.
    """
    try:
        data = get("/courses", token=token)
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        return [], f"Kunne ikke hente fag: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, list):
        return [], "Uventet svar fra serveren."
    return data, ""


def list_available_courses(token: str) -> tuple[list[dict[str, Any]], str]:
    """Fetch all courses where the authenticated user is enrolled as a student.

    Returns:
        (courses, error_message)
    """
    try:
        data = get("/courses/available", token=token)
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        return [], f"Kunne ikke hente fag: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, list):
        return [], "Uventet svar fra serveren."
    return data, ""


def list_responsible_courses(token: str) -> tuple[list[dict[str, Any]], str]:
    """Fetch courses where the authenticated user is enrolled as a teacher.

    Returns:
        (courses, error_message)
    """
    try:
        data = get("/courses/responsible", token=token)
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        return [], f"Kunne ikke hente fag: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, list):
        return [], "Uventet svar fra serveren."
    return data, ""


def create_course(
    token: str,
    name: str,
    code: str,
    chroma_collection: str,
    documents_dir: str,
    *,
    description: str | None = None,
    rag_mode: str = "kg_rag",
) -> tuple[bool, str, dict[str, Any] | None]:
    """Create a new course via the API.

    Returns:
        (success, message, course_data)
    """
    try:
        course = post(
            "/courses",
            {
                "name": name,
                "code": code,
                "chroma_collection": chroma_collection,
                "documents_dir": documents_dir,
                "description": description,
                "rag_mode": rag_mode,
            },
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 409:
            return False, "Et fag med denne koden finnes allerede.", None
        return False, f"Kunne ikke opprette fag: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(course, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "Faget ble opprettet.", course


def delete_course(token: str, course_id: str) -> tuple[bool, str]:
    """Delete a course via the API.

    Returns:
        (success, message)
    """
    try:
        delete(f"/courses/{course_id}", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt."
        if exc.status == 404:
            return False, "Faget ble ikke funnet."
        return False, f"Kunne ikke slette fag: {exc.detail}"
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}"

    return True, "Faget ble slettet."


def get_course_instructions(
    token: str,
    course_id: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Fetch the persisted course-specific tutor instructions for one course."""
    try:
        data = get(f"/courses/{course_id}/instructions", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 404:
            return False, "Fant ikke faget.", None
        return False, f"Kunne ikke hente kursinstruksjoner: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "", data


def update_course_instructions(
    token: str,
    course_id: str,
    instructions: str | None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Update course-specific tutor instructions for one course."""
    try:
        data = patch(
            f"/courses/{course_id}/instructions",
            {"course_specific_instructions": instructions},
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 404:
            return False, "Fant ikke faget.", None
        if exc.status == 422:
            return False, "Ugyldige instruksjoner.", None
        return False, f"Kunne ikke lagre kursinstruksjoner: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "Kursinstruksjoner lagret.", data


def enroll_user(
    token: str,
    course_id: str,
    user_email: str,
    *,
    role: str = "student",
) -> tuple[bool, str]:
    """Enroll a user in a course by email.

    Returns:
        (success, message)
    """
    try:
        post(
            f"/courses/{course_id}/enrollments",
            {"user_email": user_email, "role": role},
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt."
        if exc.status == 404:
            return False, f"Fant ingen bruker med e-post '{user_email}'."
        if exc.status == 409:
            return False, "Brukeren er allerede registrert i faget."
        return False, f"Kunne ikke melde inn bruker: {exc.detail}"
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}"

    return True, "Bruker lagt til i faget."


def unenroll_user(token: str, course_id: str, user_id: str) -> tuple[bool, str]:
    """Remove a user from a course.

    Returns:
        (success, message)
    """
    try:
        delete(f"/courses/{course_id}/enrollments/{user_id}", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt."
        if exc.status == 404:
            return False, "Brukeren er ikke registrert i faget."
        return False, f"Kunne ikke fjerne bruker: {exc.detail}"
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}"

    return True, "Bruker fjernet fra faget."


def preview_enrollment_import(
    token: str,
    course_id: str,
    csv_path: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Upload a CSV to stage an enrollment import preview.

    Returns:
        (success, error_message, preview_data)
    """
    path = Path(csv_path)
    try:
        content = path.read_bytes()
    except OSError as exc:
        return False, f"Kunne ikke lese filen: {exc}", None

    try:
        data = post_multipart(
            f"/courses/{course_id}/enrollment-imports/preview",
            files=[("file", path.name, content, "text/csv")],
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 400:
            return False, exc.detail, None
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 404:
            return False, "Fant ikke faget.", None
        return False, f"Feil ved forhåndsvisning: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "", data


def confirm_enrollment_import(
    token: str,
    course_id: str,
    preview_id: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Confirm a staged enrollment import, creating missing accounts and enrolling all.

    Returns:
        (success, error_message, confirmation_data)
    """
    try:
        data = post(
            f"/courses/{course_id}/enrollment-imports/{preview_id}/confirm",
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 404:
            return False, "Forhåndsvisningen er utløpt. Last opp CSV-en på nytt.", None
        if exc.status == 409:
            return False, "Konflikten oppstod under bekreftelse. Last opp CSV-en på nytt.", None
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        return False, f"Feil ved bekreftelse: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    return True, "", data


def list_course_students(
    token: str,
    course_id: str,
    *,
    page: int = 1,
    page_size: int = 100,
) -> tuple[list[dict[str, Any]], str]:
    """Fetch student users in a course."""
    try:
        data = get(
            f"/courses/{course_id}/students?page={page}&page_size={page_size}",
            token=token,
        )
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return [], "Ikke tillatt."
        if exc.status == 404:
            return [], "Fant ikke faget."
        return [], f"Kunne ikke hente studenter: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, dict):
        return [], "Uventet svar fra serveren."
    items = data.get("items")
    if not isinstance(items, list):
        return [], "Uventet svar fra serveren."
    return [item for item in items if isinstance(item, dict)], ""


def list_materials(token: str, course_id: str) -> tuple[list[dict[str, Any]], str]:
    """Fetch uploaded materials for a course."""
    try:
        data = get(f"/courses/{course_id}/documents", token=token)
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return [], "Ikke tillatt."
        if exc.status == 404:
            return [], "Fant ikke faget."
        return [], f"Kunne ikke hente materiale: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, list):
        return [], "Uventet svar fra serveren."

    materials: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        material = dict(item)
        material["size_bytes"] = 0
        materials.append(material)
    return materials, ""


def upload_material(
    token: str,
    course_id: str,
    file_path: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Upload one local file as course material."""
    path = Path(file_path)
    if not path.exists():
        return False, f"Fant ikke filen: {file_path}", None

    content = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    try:
        data = post_multipart(
            f"/courses/{course_id}/documents",
            files=[("files", path.name, content, mime)],
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 400:
            return False, f"Kunne ikke laste opp filen: {exc.detail}", None
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 404:
            return False, "Fant ikke faget.", None
        return False, f"Kunne ikke laste opp filen: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, list):
        return False, "Uventet svar fra serveren.", None

    uploaded_documents = [item for item in data if isinstance(item, dict)]
    if not uploaded_documents:
        return False, "Uventet svar fra serveren.", None
    return True, "Materiale lastet opp.", uploaded_documents[0]


def upload_zip_material(
    token: str,
    course_id: str,
    file_path: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Upload a zip archive and stage all supported files inside it as course material."""
    path = Path(file_path)
    if not path.exists():
        return False, f"Fant ikke filen: {file_path}", None

    content = path.read_bytes()
    try:
        data = post_multipart(
            f"/courses/{course_id}/documents/zip",
            files=[("file", path.name, content, "application/zip")],
            token=token,
        )
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 400:
            return False, f"Kunne ikke laste opp zip-filen: {exc.detail}", None
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 404:
            return False, "Fant ikke faget.", None
        return False, f"Kunne ikke laste opp zip-filen: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None

    staged_count = int(data.get("staged_count") or 0)
    skipped_count = int(data.get("skipped_count") or 0)
    msg = f"{path.name}: {staged_count} fil(er) stageet fra zip"
    if skipped_count:
        msg += f", {skipped_count} hoppet over"
    return True, msg, data


def delete_material(token: str, course_id: str, material_id: str) -> tuple[bool, str]:
    """Delete one uploaded course material."""
    try:
        delete(f"/courses/{course_id}/documents/{material_id}", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt."
        if exc.status == 404:
            return False, "Fant ikke materialet."
        return False, f"Kunne ikke slette materialet: {exc.detail}"
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}"

    return True, "Materiale slettet."


def start_ingestion(
    token: str,
    course_id: str,
    *,
    material_ids: list[str] | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Queue a new ingestion job for a course.

    Note: current backend applies all staged changes and ignores material_ids.
    """
    try:
        data = post(f"/courses/{course_id}/documents/confirm", token=token)
    except ApiUnauthorizedError:
        return False, "Sessionen er utløpt — logg inn på nytt.", None
    except ApiError as exc:
        if exc.status == 403:
            return False, "Ikke tillatt.", None
        if exc.status == 404:
            return False, "Fant ikke faget.", None
        if exc.status == 409:
            return False, "En oppdatering kjører allerede for dette faget.", None
        return False, f"Kunne ikke starte ingestion: {exc.detail}", None
    except Exception as exc:
        return False, f"Kunne ikke nå API-serveren: {exc}", None

    if not isinstance(data, dict):
        return False, "Uventet svar fra serveren.", None
    _ = material_ids
    return True, "Ingestering av stagede materialendringer er startet.", data


def list_ingestions(token: str, course_id: str) -> tuple[list[dict[str, Any]], str]:
    """Fetch ingestion jobs for a course, newest first."""
    try:
        data = get(f"/courses/{course_id}/documents/status", token=token)
    except ApiUnauthorizedError:
        return [], "Sessionen er utløpt — logg inn på nytt."
    except ApiError as exc:
        if exc.status == 403:
            return [], "Ikke tillatt."
        if exc.status == 404:
            return [], "Fant ikke faget."
        return [], f"Kunne ikke hente ingestion-jobber: {exc.detail}"
    except Exception as exc:
        return [], f"Kunne ikke nå API-serveren: {exc}"

    if not isinstance(data, dict):
        return [], "Uventet svar fra serveren."
    return [
        {
            "status": str(data.get("rebuild_status") or "ukjent"),
            "rebuild_error": str(data.get("rebuild_error") or "").strip(),
            "pending_additions": int(data.get("pending_additions") or 0),
            "pending_removals": int(data.get("pending_removals") or 0),
            "index_version": int(data.get("index_version") or 0),
            "active_scope": str(data.get("active_scope") or "").strip(),
        }
    ], ""
