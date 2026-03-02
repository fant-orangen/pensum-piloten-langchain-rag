"""Main Gradio app with auth, student page, and internal routing."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.services import ensure_admin_user
from src.ui.pages import (
    AB_PAGE_CSS,
    build_ab_page,
    build_admin_page,
    build_auth_page,
    build_chat_page,
    build_student_page,
    handle_admin_refresh,
    handle_back_to_student,
    handle_login,
    handle_logout,
    handle_open_ab_compare,
    handle_open_chat,
    handle_register,
    handle_upgrade_user,
)
from src.ui.router import ROUTE_ADMIN, route_visibility_updates
from src.ui.state import ROUTE_KEY, default_app_state, student_name_text, user_role


def _render_main_app(
    state: dict[str, Any],
    *,
    login_message: str = "",
    register_message: str = "",
    student_message: str = "",
) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    if state.get(ROUTE_KEY) == ROUTE_ADMIN and user_role(state) != "admin":
        state = default_app_state()
    if state.get(ROUTE_KEY) == ROUTE_ADMIN and user_role(state) == "admin":
        admin_users_update, admin_status = handle_admin_refresh(state)
    else:
        admin_users_update = gr.update(value=None)
        admin_status = ""
    return (
        state,
        *route_visibility_updates(state.get(ROUTE_KEY)),
        admin_users_update,
        admin_status,
        student_name_text(state),
        student_message,
        login_message,
        register_message,
    )

def _handle_upgrade_user(
    state: dict[str, Any],
    username: str | None,
) -> tuple[Any, str]:
    return handle_upgrade_user(state, username)


def _handle_login(username: str, password: str) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    state, login_message, register_message, student_message = handle_login(username, password)
    return _render_main_app(
        state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_register(
    username: str,
    password: str,
    password_confirm: str,
    firstname: str,
    surname: str,
) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    state, login_message, register_message, student_message = handle_register(
        username,
        password,
        password_confirm,
        firstname,
        surname,
    )
    return _render_main_app(
        state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_open_ab_compare(
    state: dict[str, Any],
) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    next_state, login_message, register_message, student_message = handle_open_ab_compare(state)
    return _render_main_app(
        next_state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_open_chat(
    state: dict[str, Any],
) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    next_state, login_message, register_message, student_message = handle_open_chat(state)
    return _render_main_app(
        next_state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_back_to_student(
    state: dict[str, Any],
) -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    next_state, login_message, register_message, student_message = handle_back_to_student(state)
    return _render_main_app(
        next_state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_logout() -> tuple[dict[str, Any], Any, Any, Any, Any, Any, Any, str, str, str, str, str]:
    state, login_message, register_message, student_message = handle_logout()
    return _render_main_app(
        state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def build_main_app() -> gr.Blocks:
    ensure_admin_user()

    with gr.Blocks(css=AB_PAGE_CSS, title="Pensum Piloten") as demo:
        app_state = gr.State(default_app_state())

        auth_page = build_auth_page(visible=True)
        student_page = build_student_page(visible=False)
        ab_page = build_ab_page(demo, visible=False, include_back_button=True)
        chat_page = build_chat_page(visible=False)
        admin_page = build_admin_page(visible=False)

        app_outputs = [
            app_state,
            auth_page.group,
            student_page.group,
            ab_page.group,
            chat_page.group,
            admin_page.group,
            admin_page.users_dropdown,
            admin_page.status_text,
            student_page.name_text,
            student_page.status_text,
            auth_page.login_status,
            auth_page.register_status,
        ]

        auth_page.login_button.click(
            fn=_handle_login,
            inputs=[auth_page.login_username, auth_page.login_password],
            outputs=app_outputs,
        )
        auth_page.register_button.click(
            fn=_handle_register,
            inputs=[
                auth_page.register_username,
                auth_page.register_password,
                auth_page.register_password_confirm,
                auth_page.register_firstname,
                auth_page.register_surname,
            ],
            outputs=app_outputs,
        )
        student_page.open_ab_button.click(
            fn=_handle_open_ab_compare,
            inputs=[app_state],
            outputs=app_outputs,
        )
        student_page.open_chat_button.click(
            fn=_handle_open_chat,
            inputs=[app_state],
            outputs=app_outputs,
        )
        student_page.logout_button.click(
            fn=_handle_logout,
            inputs=None,
            outputs=app_outputs,
        )
        if ab_page.back_button is not None:
            ab_page.back_button.click(
                fn=_handle_back_to_student,
                inputs=[app_state],
                outputs=app_outputs,
            )
        chat_page.back_button.click(
            fn=_handle_back_to_student,
            inputs=[app_state],
            outputs=app_outputs,
        )
        admin_page.upgrade_button.click(
            fn=_handle_upgrade_user,
            inputs=[app_state, admin_page.users_dropdown],
            outputs=[admin_page.users_dropdown, admin_page.status_text],
        )
        admin_page.logout_button.click(
            fn=_handle_logout,
            inputs=None,
            outputs=app_outputs,
        )

    return demo
