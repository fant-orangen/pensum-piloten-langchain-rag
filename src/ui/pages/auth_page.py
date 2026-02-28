"""Auth page UI and handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gradio as gr

from src.services import login_user, register_user
from src.ui.state import authenticated_app_state, default_app_state


@dataclass(slots=True)
class AuthPageComponents:
    group: gr.Group
    login_username: gr.Textbox
    login_password: gr.Textbox
    login_button: gr.Button
    login_status: gr.Markdown
    register_username: gr.Textbox
    register_password: gr.Textbox
    register_name: gr.Textbox
    register_button: gr.Button
    register_status: gr.Markdown


def build_auth_page(*, visible: bool) -> AuthPageComponents:
    with gr.Group(visible=visible) as group:
        with gr.Tabs():
            with gr.Tab("Logg inn"):
                gr.Markdown("# Logg inn")
                login_username = gr.Textbox(label="Brukernavn")
                login_password = gr.Textbox(label="Passord", type="password")
                login_button = gr.Button("Logg inn", variant="primary")
                login_status = gr.Markdown()

            with gr.Tab("Registrer"):
                gr.Markdown("# Registrer")
                register_username = gr.Textbox(label="Brukernavn")
                register_password = gr.Textbox(label="Passord", type="password")
                register_name = gr.Textbox(label="Navn")
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
        register_name=register_name,
        register_button=register_button,
        register_status=register_status,
    )


def handle_login(username: str, password: str) -> tuple[dict[str, Any], str, str, str]:
    success, message, user = login_user(username, password)
    if not success or user is None:
        return default_app_state(), message, "", ""

    return authenticated_app_state(user.username, user.name), "", "", message


def handle_register(username: str, password: str, name: str) -> tuple[dict[str, Any], str, str, str]:
    success, message, user = register_user(username, password, name)
    if not success or user is None:
        return default_app_state(), "", message, ""

    return authenticated_app_state(user.username, user.name), "", "", message
