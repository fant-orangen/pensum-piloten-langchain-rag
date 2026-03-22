"""State helpers for the Gradio app."""

from __future__ import annotations

from typing import Any

from src.ui.router import ROUTE_ADMIN, ROUTE_AUTH, ROUTE_STUDENT, ROUTE_TEACHER, normalise_route

ROUTE_KEY = "route"
LOGGED_IN_KEY = "logged_in"
USERNAME_KEY = "username"
NAME_KEY = "name"
FIRSTNAME_KEY = "firstname"
SURNAME_KEY = "surname"
ROLE_KEY = "role"
COURSE_ID_KEY = "course_id"
COURSE_NAME_KEY = "course_name"
TOKEN_KEY = "token"
ENROLLMENT_PREVIEW_ID_KEY = "enrollment_preview_id"


def normalise_role(role: str | None) -> str:
    cleaned = str(role or "").strip().lower()
    if cleaned == "admin":
        return "admin"
    if cleaned == "teacher":
        return "teacher"
    return "student"


def default_app_state() -> dict[str, Any]:
    return {
        ROUTE_KEY: ROUTE_AUTH,
        LOGGED_IN_KEY: False,
        USERNAME_KEY: None,
        NAME_KEY: None,
        FIRSTNAME_KEY: None,
        SURNAME_KEY: None,
        ROLE_KEY: None,
        COURSE_ID_KEY: None,
        COURSE_NAME_KEY: None,
        TOKEN_KEY: None,
    }


def authenticated_app_state(
    username: str,
    firstname: str,
    surname: str,
    role: str = "student",
    *,
    token: str | None = None,
) -> dict[str, Any]:
    normalised_role = normalise_role(role)
    full_name = " ".join(part for part in (firstname.strip(), surname.strip()) if part)
    route = home_route_for_role(normalised_role)
    return {
        ROUTE_KEY: route,
        LOGGED_IN_KEY: True,
        USERNAME_KEY: username,
        NAME_KEY: full_name or None,
        FIRSTNAME_KEY: firstname,
        SURNAME_KEY: surname,
        ROLE_KEY: normalised_role,
        COURSE_ID_KEY: None,
        COURSE_NAME_KEY: None,
        TOKEN_KEY: token,
    }


def home_route_for_role(role: str | None) -> str:
    normalised_role = normalise_role(role)
    if normalised_role == "admin":
        return ROUTE_ADMIN
    if normalised_role == "teacher":
        return ROUTE_TEACHER
    return ROUTE_STUDENT


def with_route(state: dict[str, Any], route: str) -> dict[str, Any]:
    next_state = dict(state)
    next_state[ROUTE_KEY] = normalise_route(route)
    return next_state


def with_selected_course(
    state: dict[str, Any],
    course_id: str | None,
    *,
    route: str | None = None,
    course_name: str | None = None,
) -> dict[str, Any]:
    next_state = dict(state)
    next_state[COURSE_ID_KEY] = course_id
    next_state[COURSE_NAME_KEY] = course_name
    if route is not None:
        next_state[ROUTE_KEY] = normalise_route(route)
    return next_state


def clear_selected_course(state: dict[str, Any]) -> dict[str, Any]:
    next_state = dict(state)
    next_state[COURSE_ID_KEY] = None
    next_state[COURSE_NAME_KEY] = None
    return next_state


def is_logged_in(state: dict[str, Any]) -> bool:
    return bool(state.get(LOGGED_IN_KEY))


def user_role(state: dict[str, Any]) -> str:
    role = state.get(ROLE_KEY)
    if isinstance(role, str) and role:
        return normalise_role(role)
    return normalise_role(None)


def auth_token(state: dict[str, Any]) -> str | None:
    token = state.get(TOKEN_KEY)
    if isinstance(token, str) and token:
        return token
    return None


def student_name_text(state: dict[str, Any]) -> str:
    firstname = str(state.get(FIRSTNAME_KEY) or "").strip()
    surname = str(state.get(SURNAME_KEY) or "").strip()
    full_name = " ".join(part for part in (firstname, surname) if part)
    if not full_name:
        full_name = str(state.get(NAME_KEY) or "").strip()
    return f"Navn: {full_name or '-'}"
