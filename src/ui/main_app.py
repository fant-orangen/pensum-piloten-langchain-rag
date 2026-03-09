"""Main Gradio app with auth, role-based home pages, and internal routing."""

from __future__ import annotations

from typing import Any

import gradio as gr

from src.ui.pages import (
    AB_PAGE_CSS,
    build_ab_page,
    build_admin_page,
    build_auth_page,
    build_chat_page,
    build_student_course_page,
    build_student_page,
    build_teacher_course_page,
    build_teacher_page,
    handle_add_course,
    handle_add_student,
    handle_delete_material,
    handle_admin_refresh,
    handle_back_to_student,
    handle_login,
    handle_logout,
    handle_open_ab_compare,
    handle_open_chat,
    handle_open_responsible_course,
    handle_open_student_course,
    handle_open_teacher_course,
    handle_refresh_ingestion,
    handle_register,
    handle_start_ingestion,
    handle_upload_materials,
    handle_upgrade_user,
    handle_view_as_student,
    student_course_title_text,
    student_courses_update,
    teacher_available_courses_update,
    teacher_course_ingestion_status_text,
    teacher_course_material_choices_update,
    teacher_course_student_choices_update,
    teacher_course_students_text,
    teacher_course_title_text,
    teacher_name_text,
    teacher_responsible_courses_update,
)
from src.ui.router import (
    ROUTE_ADMIN,
    ROUTE_STUDENT,
    ROUTE_STUDENT_COURSE,
    ROUTE_TEACHER,
    ROUTE_TEACHER_COURSE,
    route_visibility_updates,
)
from src.ui.state import (
    COURSE_ID_KEY,
    auth_token,
    clear_selected_course,
    default_app_state,
    home_route_for_role,
    is_logged_in,
    student_name_text,
    user_role,
    with_route,
)


def _render_main_app(
    state: dict[str, Any],
    *,
    login_message: str = "",
    register_message: str = "",
    student_message: str = "",
    teacher_message: str = "",
) -> tuple[Any, ...]:
    if not is_logged_in(state):
        state = default_app_state()
    else:
        current_role = user_role(state)
        current_route = state.get("route")

        if current_route == ROUTE_ADMIN and current_role != "admin":
            state = with_route(clear_selected_course(state), home_route_for_role(current_role))
        elif current_route == ROUTE_TEACHER and current_role != "teacher":
            state = with_route(clear_selected_course(state), home_route_for_role(current_role))
        elif current_route == ROUTE_TEACHER_COURSE:
            if current_role != "teacher":
                state = with_route(clear_selected_course(state), home_route_for_role(current_role))
            else:
                course_id = str(state.get(COURSE_ID_KEY) or "").strip()
                if not course_id:
                    state = with_route(clear_selected_course(state), ROUTE_TEACHER)
                    teacher_message = teacher_message or "Fant ikke faget."
        elif current_route == ROUTE_STUDENT_COURSE:
            if current_role != "student":
                state = with_route(clear_selected_course(state), home_route_for_role(current_role))
            else:
                course_id = str(state.get(COURSE_ID_KEY) or "").strip()
                if not course_id:
                    state = with_route(clear_selected_course(state), ROUTE_STUDENT)
                    student_message = student_message or "Fant ikke faget."

    current_role = user_role(state)
    current_route = state.get("route")

    if current_route == ROUTE_ADMIN and current_role == "admin":
        admin_users_update, admin_status = handle_admin_refresh(state)
    else:
        admin_users_update = gr.update(value=None)
        admin_status = ""

    if current_route == ROUTE_ADMIN and current_role == "admin" and student_message:
        admin_status = f"{student_message}\n\n{admin_status}" if admin_status else student_message

    student_status = student_message if current_route == ROUTE_STUDENT and current_role == "student" else ""
    teacher_status = teacher_message if current_route == ROUTE_TEACHER and current_role == "teacher" else ""

    token = auth_token(state)

    course_id = str(state.get(COURSE_ID_KEY) or "").strip() or None

    return (
        state,
        *route_visibility_updates(current_route),
        admin_users_update,
        admin_status,
        student_name_text(state),
        student_courses_update(state),
        student_status,
        teacher_name_text(state),
        teacher_responsible_courses_update(state),
        teacher_available_courses_update(state),
        teacher_status,
        teacher_course_title_text(state),
        teacher_course_students_text(state),
        teacher_course_material_choices_update(state),
        teacher_course_student_choices_update(state),
        teacher_course_ingestion_status_text(state),
        "",
        student_course_title_text(state),
        login_message,
        register_message,
        token,
        course_id,
        current_route,
    )


def _handle_upgrade_user(state: dict[str, Any], username: str | None) -> tuple[Any, str]:
    return handle_upgrade_user(state, username)


def _handle_add_course(state: dict[str, Any], course_name: str) -> tuple[str, Any, Any, str]:
    return handle_add_course(state, course_name)


def _handle_add_student(state: dict[str, Any], student_username: str | None) -> tuple[Any, str, str]:
    return handle_add_student(state, student_username)


def _handle_upload_materials(
    state: dict[str, Any],
    file_paths: str | list[str] | None,
) -> tuple[Any, Any, str]:
    return handle_upload_materials(state, file_paths)


def _handle_delete_material(
    state: dict[str, Any],
    material_ids: list[str] | None,
) -> tuple[Any, str]:
    return handle_delete_material(state, material_ids)


def _handle_refresh_materials(state: dict[str, Any]) -> tuple[Any]:
    return (teacher_course_material_choices_update(state),)


def _handle_start_ingestion(
    state: dict[str, Any],
    selected_material_ids: list[str] | None,
) -> tuple[Any, str, str]:
    return handle_start_ingestion(state, selected_material_ids)


def _handle_refresh_ingestion(state: dict[str, Any]) -> tuple[str, str]:
    return handle_refresh_ingestion(state)


def _handle_open_responsible_course(state: dict[str, Any], course_id: str | None) -> tuple[Any, ...]:
    next_state, teacher_message = handle_open_responsible_course(state, course_id)
    return _render_main_app(next_state, teacher_message=teacher_message)


def _handle_open_teacher_course(state: dict[str, Any], course_id: str | None) -> tuple[Any, ...]:
    next_state, teacher_message = handle_open_teacher_course(state, course_id)
    return _render_main_app(next_state, teacher_message=teacher_message)


def _handle_open_student_course(state: dict[str, Any], course_id: str | None) -> tuple[Any, ...]:
    next_state, student_message = handle_open_student_course(state, course_id)
    return _render_main_app(next_state, student_message=student_message)


def _handle_login(username: str, password: str) -> tuple[Any, ...]:
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
) -> tuple[Any, ...]:
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


def _handle_open_ab_compare(state: dict[str, Any]) -> tuple[Any, ...]:
    next_state, login_message, register_message, student_message = handle_open_ab_compare(state)
    return _render_main_app(
        next_state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_open_chat(state: dict[str, Any]) -> tuple[Any, ...]:
    next_state, login_message, register_message, student_message = handle_open_chat(state)
    return _render_main_app(
        next_state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_view_as_student(state: dict[str, Any]) -> tuple[Any, ...]:
    next_state, teacher_message = handle_view_as_student(state)
    return _render_main_app(next_state, teacher_message=teacher_message)


def _handle_back_to_home(state: dict[str, Any]) -> tuple[Any, ...]:
    next_state, login_message, register_message, student_message = handle_back_to_student(state)
    return _render_main_app(
        next_state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def _handle_logout() -> tuple[Any, ...]:
    state, login_message, register_message, student_message = handle_logout()
    return _render_main_app(
        state,
        login_message=login_message,
        register_message=register_message,
        student_message=student_message,
    )


def build_main_app() -> gr.Blocks:
    with gr.Blocks(css=AB_PAGE_CSS, title="Pensum Piloten") as demo:
        app_state = gr.State(default_app_state())

        auth_page = build_auth_page(visible=True)
        student_page = build_student_page(visible=False)
        teacher_page = build_teacher_page(visible=False)
        ab_page = build_ab_page(demo, visible=False, include_back_button=True)
        chat_page = build_chat_page(visible=False)
        admin_page = build_admin_page(visible=False)
        teacher_course_page = build_teacher_course_page(visible=False)
        student_course_page = build_student_course_page(visible=False)

        app_outputs = [
            app_state,
            auth_page.group,
            student_page.group,
            teacher_page.group,
            ab_page.group,
            chat_page.group,
            admin_page.group,
            teacher_course_page.group,
            student_course_page.group,
            admin_page.users_dropdown,
            admin_page.status_text,
            student_page.name_text,
            student_page.courses_list,
            student_page.status_text,
            teacher_page.name_text,
            teacher_page.responsible_list,
            teacher_page.available_list,
            teacher_page.status_text,
            teacher_course_page.course_title,
            teacher_course_page.students_list,
            teacher_course_page.materials_list,
            teacher_course_page.add_student_username,
            teacher_course_page.ingestion_status,
            teacher_course_page.status_text,
            student_course_page.course_title,
            auth_page.login_status,
            auth_page.register_status,
            chat_page.token_state,
            chat_page.course_id_state,
            chat_page.route_state,
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
        student_page.courses_list.change(
            fn=_handle_open_student_course,
            inputs=[app_state, student_page.courses_list],
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
        teacher_page.responsible_list.change(
            fn=_handle_open_responsible_course,
            inputs=[app_state, teacher_page.responsible_list],
            outputs=app_outputs,
        )
        teacher_page.available_list.change(
            fn=_handle_open_teacher_course,
            inputs=[app_state, teacher_page.available_list],
            outputs=app_outputs,
        )
        teacher_page.add_course_button.click(
            fn=_handle_add_course,
            inputs=[app_state, teacher_page.add_course_name],
            outputs=[
                teacher_page.add_course_name,
                teacher_page.responsible_list,
                teacher_page.available_list,
                teacher_page.status_text,
            ],
        )
        teacher_page.logout_button.click(
            fn=_handle_logout,
            inputs=None,
            outputs=app_outputs,
        )
        teacher_course_page.add_student_button.click(
            fn=_handle_add_student,
            inputs=[app_state, teacher_course_page.add_student_username],
            outputs=[
                teacher_course_page.add_student_username,
                teacher_course_page.students_list,
                teacher_course_page.status_text,
            ],
        )
        teacher_course_page.upload_button.click(
            fn=_handle_upload_materials,
            inputs=[app_state, teacher_course_page.upload_files],
            outputs=[
                teacher_course_page.upload_files,
                teacher_course_page.materials_list,
                teacher_course_page.status_text,
            ],
        )
        teacher_course_page.delete_material_button.click(
            fn=_handle_delete_material,
            inputs=[app_state, teacher_course_page.materials_list],
            outputs=[
                teacher_course_page.materials_list,
                teacher_course_page.status_text,
            ],
        )
        teacher_course_page.refresh_materials_button.click(
            fn=_handle_refresh_materials,
            inputs=[app_state],
            outputs=[
                teacher_course_page.materials_list,
            ],
        )
        teacher_course_page.start_ingestion_button.click(
            fn=_handle_start_ingestion,
            inputs=[app_state, teacher_course_page.materials_list],
            outputs=[
                teacher_course_page.materials_list,
                teacher_course_page.ingestion_status,
                teacher_course_page.status_text,
            ],
        )
        teacher_course_page.refresh_ingestion_button.click(
            fn=_handle_refresh_ingestion,
            inputs=[app_state],
            outputs=[
                teacher_course_page.ingestion_status,
                teacher_course_page.status_text,
            ],
        )
        teacher_course_page.view_as_student_button.click(
            fn=_handle_view_as_student,
            inputs=[app_state],
            outputs=app_outputs,
        )
        teacher_course_page.back_button.click(
            fn=_handle_back_to_home,
            inputs=[app_state],
            outputs=app_outputs,
        )
        student_course_page.back_button.click(
            fn=_handle_back_to_home,
            inputs=[app_state],
            outputs=app_outputs,
        )
        if ab_page.back_button is not None:
            ab_page.back_button.click(
                fn=_handle_back_to_home,
                inputs=[app_state],
                outputs=app_outputs,
            )
        chat_page.back_button.click(
            fn=_handle_back_to_home,
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
