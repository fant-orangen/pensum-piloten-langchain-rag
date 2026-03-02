"""State helpers for the Gradio app."""

from __future__ import annotations

from typing import Any

from src.ui.router import ROUTE_ADMIN, ROUTE_AUTH, ROUTE_STUDENT, normalise_route

ROUTE_KEY = "route"
LOGGED_IN_KEY = "logged_in"
USERNAME_KEY = "username"
NAME_KEY = "name"
FIRSTNAME_KEY = "firstname"
SURNAME_KEY = "surname"
ROLE_KEY = "role"


def default_app_state() -> dict[str, Any]:
    return {
        ROUTE_KEY: ROUTE_AUTH,
        LOGGED_IN_KEY: False,
        USERNAME_KEY: None,
        NAME_KEY: None,
        FIRSTNAME_KEY: None,
        SURNAME_KEY: None,
        ROLE_KEY: None,
    }


def authenticated_app_state(
    username: str,
    firstname: str,
    surname: str,
    role: str = "student",
) -> dict[str, Any]:
    full_name = " ".join(part for part in (firstname.strip(), surname.strip()) if part)
    route = ROUTE_ADMIN if role == "admin" else ROUTE_STUDENT
    return {
        ROUTE_KEY: route,
        LOGGED_IN_KEY: True,
        USERNAME_KEY: username,
        NAME_KEY: full_name or None,
        FIRSTNAME_KEY: firstname,
        SURNAME_KEY: surname,
        ROLE_KEY: role,
    }


def with_route(state: dict[str, Any], route: str) -> dict[str, Any]:
    next_state = dict(state)
    next_state[ROUTE_KEY] = normalise_route(route)
    return next_state


def is_logged_in(state: dict[str, Any]) -> bool:
    return bool(state.get(LOGGED_IN_KEY))


def user_role(state: dict[str, Any]) -> str:
    role = state.get(ROLE_KEY)
    if isinstance(role, str) and role:
        return role
    return "student"


def student_name_text(state: dict[str, Any]) -> str:
    firstname = str(state.get(FIRSTNAME_KEY) or "").strip()
    surname = str(state.get(SURNAME_KEY) or "").strip()
    full_name = " ".join(part for part in (firstname, surname) if part)
    if not full_name:
        full_name = str(state.get(NAME_KEY) or "").strip()
    return f"Navn: {full_name or '-'}"
