"""State helpers for the Gradio app."""

from __future__ import annotations

from typing import Any

from src.ui.router import ROUTE_AUTH, ROUTE_STUDENT, normalise_route

ROUTE_KEY = "route"
LOGGED_IN_KEY = "logged_in"
USERNAME_KEY = "username"
NAME_KEY = "name"


def default_app_state() -> dict[str, Any]:
    return {
        ROUTE_KEY: ROUTE_AUTH,
        LOGGED_IN_KEY: False,
        USERNAME_KEY: None,
        NAME_KEY: None,
    }


def authenticated_app_state(username: str, name: str) -> dict[str, Any]:
    return {
        ROUTE_KEY: ROUTE_STUDENT,
        LOGGED_IN_KEY: True,
        USERNAME_KEY: username,
        NAME_KEY: name,
    }


def with_route(state: dict[str, Any], route: str) -> dict[str, Any]:
    next_state = dict(state)
    next_state[ROUTE_KEY] = normalise_route(route)
    return next_state


def is_logged_in(state: dict[str, Any]) -> bool:
    return bool(state.get(LOGGED_IN_KEY))


def student_name_text(state: dict[str, Any]) -> str:
    return f"Navn: {state.get(NAME_KEY) or '-'}"
