"""Auth page UI and handlers.

Provides the login and registration interface and the handlers that authenticate
users against the backend, derive their role, and populate the shared app state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

import src.ui.services.auth_service as _auth_api
from src.ui.state import authenticated_app_state, default_app_state


@dataclass(slots=True)
class AuthPageComponents:
    """Holds references to every Gradio component on the auth page."""

    group: gr.Group
    login_username: gr.Textbox
    login_password: gr.Textbox
    login_button: gr.Button
    login_status: gr.Markdown
    register_username: gr.Textbox
    register_password: gr.Textbox
    register_password_confirm: gr.Textbox
    register_firstname: gr.Textbox
    register_surname: gr.Textbox
    register_button: gr.Button
    register_status: gr.Markdown


def build_auth_page(*, visible: bool) -> AuthPageComponents:
    """Build and return the login/registration Gradio group."""
    with gr.Group(visible=visible) as group:
        with gr.Tabs():
            with gr.Tab("Logg inn"):
                gr.Markdown("# Logg inn")
                login_username = gr.Textbox(label="E-post")
                login_password = gr.Textbox(label="Passord", type="password")
                login_button = gr.Button("Logg inn", variant="primary")
                login_status = gr.Markdown()

            with gr.Tab("Registrer"):
                gr.Markdown("# Registrer")
                register_username = gr.Textbox(label="E-post")
                register_password = gr.Textbox(label="Passord", type="password")
                register_password_confirm = gr.Textbox(label="Gjenta passord", type="password")
                register_firstname = gr.Textbox(label="Fornavn")
                register_surname = gr.Textbox(label="Etternavn")
                register_button = gr.Button("Registrer", variant="primary")
                register_status = gr.Markdown()

    return AuthPageComponents(
        group=group,
        login_username=login_username,
        login_password=login_password,
        login_button=login_button,
        login_status=login_status,
        register_username=register_username,
        register_password=register_password,
        register_password_confirm=register_password_confirm,
        register_firstname=register_firstname,
        register_surname=register_surname,
        register_button=register_button,
        register_status=register_status,
    )


def handle_login(email: str, password: str) -> tuple[dict[str, Any], str, str, str]:
    """Authenticate the user and return an updated app state with the appropriate role assigned."""
    success, message, info = _auth_api.login(email.strip(), password)
    if not success or info is None:
        return default_app_state(), message, "", ""

    token = info.get("token", "")
    profile_success, profile_error, profile = _auth_api.current_user(token)
    if not profile_success or profile is None:
        return default_app_state(), profile_error or "Kunne ikke hente brukerprofil.", "", ""

    state = authenticated_app_state(
        str(profile.get("email", email.strip()) or email.strip()),
        str(profile.get("first_name", "") or ""),
        str(profile.get("last_name", "") or ""),
        str(profile.get("global_role", "student") or "student"),
        token=token,
    )
    return state, "", "", message


def handle_register(
    email: str,
    password: str,
    password_confirm: str,
    firstname: str,
    surname: str,
) -> tuple[dict[str, Any], str, str, str]:
    """Register a new user and, on success, automatically log them in and return an authenticated app state."""
    success, message, user_data = _auth_api.register(
        email.strip(),
        password,
        password_confirm,
        firstname.strip(),
        surname.strip(),
    )
    if not success or user_data is None:
        return default_app_state(), "", message, ""

    # After registration, log the user in immediately to obtain a token.
    login_success, login_message, login_info = _auth_api.login(email.strip(), password)
    if not login_success or login_info is None:
        # Registration succeeded but auto-login failed; send the user to the
        # login page with a prompt to log in manually.
        return default_app_state(), "", "Registrering fullført. Logg inn for å fortsette.", ""

    token = login_info.get("token", "")
    global_role = user_data.get("global_role", "student")
    first_name = user_data.get("first_name", firstname.strip())
    last_name = user_data.get("last_name", surname.strip())
    state = authenticated_app_state(
        email.strip(), first_name, last_name, global_role, token=token
    )
    return state, "", "", message
