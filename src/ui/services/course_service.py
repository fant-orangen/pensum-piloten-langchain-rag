"""Course service — wraps /courses/* API endpoints."""

from __future__ import annotations

from typing import Any

from src.ui.services.api_client import ApiError, ApiUnauthorizedError, delete, get, post


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
    """Fetch all courses the authenticated user is enrolled in (any role).

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
