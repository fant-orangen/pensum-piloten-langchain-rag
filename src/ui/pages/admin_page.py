"""Admin page UI and handlers.

Provides the admin interface for listing non-admin users and upgrading them to
the teacher role, accessible only to users with the admin role.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.storage import load_users
from src.services import upgrade_user_to_teacher
from src.ui.state import is_logged_in, user_role


@dataclass(slots=True)
class AdminPageComponents:
    """Holds references to every Gradio component on the admin page."""

    group: gr.Group
    users_dropdown: gr.Dropdown
    upgrade_button: gr.Button
    status_text: gr.Markdown
    logout_button: gr.Button


def _user_label(username: str, user: Any) -> str:
    """Format a human-readable label for a user showing their name and current role."""
    full_name = user.name or username
    role = user.role if isinstance(getattr(user, "role", None), str) and user.role else "student"
    return f"{username} - {full_name} ({role})"


def _non_admin_user_choices() -> list[tuple[str, str]]:
    """Return a sorted list of (label, username) pairs for all non-admin users."""
    users = load_users()
    choices: list[tuple[str, str]] = []
    for username in sorted(users):
        user = users[username]
        if user.role == "admin":
            continue
        choices.append((_user_label(username, user), username))
    return choices


def build_admin_page(*, visible: bool) -> AdminPageComponents:
    """Build and return the admin Gradio group pre-populated with non-admin users."""
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
    """Refresh the users dropdown, rejecting the request if the caller is not an admin."""
    if not is_logged_in(state) or user_role(state) != "admin":
        return gr.update(choices=_non_admin_user_choices(), value=None), "Ikke tillatt."

    choices = _non_admin_user_choices()
    if choices:
        return gr.update(choices=choices), ""
    return gr.update(choices=choices, value=None), "Ingen brukere tilgjengelig."


def handle_upgrade_user(state: dict[str, Any], username: str | None) -> tuple[Any, str]:
    """Upgrade the selected user to the teacher role and refresh the dropdown."""
    if not is_logged_in(state) or user_role(state) != "admin":
        return gr.update(choices=_non_admin_user_choices(), value=None), "Ikke tillatt."
    if not isinstance(username, str) or not username.strip():
        return gr.update(choices=_non_admin_user_choices(), value=None), "Fant ikke brukeren."

    success, message = upgrade_user_to_teacher(username)
    choices = _non_admin_user_choices()
    selected_value = username if success and any(value == username for _, value in choices) else None
    return gr.update(choices=choices, value=selected_value), message
