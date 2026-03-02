"""Admin page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.storage import load_users
from src.services import upgrade_user_to_teacher
from src.ui.state import is_logged_in, user_role


@dataclass(slots=True)
class AdminPageComponents:
    group: gr.Group
    users_dropdown: gr.Dropdown
    upgrade_button: gr.Button
    status_text: gr.Markdown
    logout_button: gr.Button


def _user_label(username: str, user: Any) -> str:
    full_name = user.name or username
    role = user.role if isinstance(getattr(user, "role", None), str) and user.role else "student"
    return f"{username} - {full_name} ({role})"


def _non_admin_user_choices() -> list[tuple[str, str]]:
    users = load_users()
    choices: list[tuple[str, str]] = []
    for username in sorted(users):
        user = users[username]
        if user.role == "admin":
            continue
        choices.append((_user_label(username, user), username))
    return choices


def build_admin_page(*, visible: bool) -> AdminPageComponents:
    initial_choices = _non_admin_user_choices()

    with gr.Group(visible=visible) as group:
        gr.Markdown("# Admin")
        gr.Markdown("Oppgrader studenter til lærere.")
        users_dropdown = gr.Dropdown(
            choices=initial_choices,
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
        return gr.update(choices=_non_admin_user_choices(), value=None), "Ikke tillatt."

    choices = _non_admin_user_choices()
    if choices:
        return gr.update(choices=choices), ""
    return gr.update(choices=choices, value=None), "Ingen brukere tilgjengelig."


def handle_upgrade_user(state: dict[str, Any], username: str | None) -> tuple[Any, str]:
    if not is_logged_in(state) or user_role(state) != "admin":
        return gr.update(choices=_non_admin_user_choices(), value=None), "Ikke tillatt."
    if not isinstance(username, str) or not username.strip():
        return gr.update(choices=_non_admin_user_choices(), value=None), "Fant ikke brukeren."

    success, message = upgrade_user_to_teacher(username)
    choices = _non_admin_user_choices()
    selected_value = username if success and any(value == username for _, value in choices) else None
    return gr.update(choices=choices, value=selected_value), message
