"""Admin page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.admin_service as _admin_api
from src.ui.state import auth_token, is_logged_in, user_role


@dataclass(slots=True)
class AdminPageComponents:
    group: gr.Group
    users_dropdown: gr.Dropdown
    upgrade_button: gr.Button
    status_text: gr.Markdown
    logout_button: gr.Button


def _normalise_role_label(role: object) -> str:
    if not isinstance(role, str):
        return "student"
    if role in {"student", "teacher", "admin"}:
        return role
    return "student"


def _user_label(user: dict[str, Any]) -> str:
    email = str(user.get("email", "") or "")
    first_name = str(user.get("first_name", "") or "").strip()
    last_name = str(user.get("last_name", "") or "").strip()
    full_name = " ".join(part for part in (first_name, last_name) if part) or email
    role = _normalise_role_label(user.get("global_role"))
    return f"{email} - {full_name} ({role})"


def _non_admin_user_choices(token: str) -> tuple[list[tuple[str, str]], str]:
    users, error = _admin_api.list_users(token)
    if error:
        return [], error

    choices: list[tuple[str, str]] = []
    for user in users:
        user_id = str(user.get("id", "") or "").strip()
        if not user_id:
            continue
        if _normalise_role_label(user.get("global_role")) == "admin":
            continue
        choices.append((_user_label(user), user_id))
    return choices, ""


def build_admin_page(*, visible: bool) -> AdminPageComponents:
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Admin")
        gr.Markdown("Oppgrader studenter til lærere.")
        users_dropdown = gr.Dropdown(
            choices=[],
            value=None,
            label="Brukere",
        )
        with gr.Row():
            upgrade_button = gr.Button("Oppgrader til lærer", variant="primary")
        status_text = gr.Markdown()
        logout_button = gr.Button("Logg ut")

    return AdminPageComponents(
        group=group,
        users_dropdown=users_dropdown,
        upgrade_button=upgrade_button,
        status_text=status_text,
        logout_button=logout_button,
    )


def handle_admin_refresh(state: dict[str, Any]) -> tuple[Any, str]:
    if not is_logged_in(state) or user_role(state) != "admin":
        return gr.update(choices=[], value=None), "Ikke tillatt."

    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=None), "Sessionen er utløpt — logg inn på nytt."

    choices, error = _non_admin_user_choices(token)
    if error:
        return gr.update(choices=[], value=None), error
    if choices:
        return gr.update(choices=choices), ""
    return gr.update(choices=choices, value=None), "Ingen brukere tilgjengelig."


def handle_upgrade_user(state: dict[str, Any], username: str | None) -> tuple[Any, str]:
    if not is_logged_in(state) or user_role(state) != "admin":
        return gr.update(choices=[], value=None), "Ikke tillatt."
    token = auth_token(state)
    if not token:
        return gr.update(choices=[], value=None), "Sessionen er utløpt — logg inn på nytt."
    if not isinstance(username, str) or not username.strip():
        choices, error = _non_admin_user_choices(token)
        if error:
            return gr.update(choices=[], value=None), error
        return gr.update(choices=choices, value=None), "Fant ikke brukeren."

    success, message = _admin_api.promote_user_to_teacher(token, username)
    choices, error = _non_admin_user_choices(token)
    if error:
        return gr.update(choices=[], value=None), error
    selected_value = username if success and any(value == username for _, value in choices) else None
    return gr.update(choices=choices, value=selected_value), message
