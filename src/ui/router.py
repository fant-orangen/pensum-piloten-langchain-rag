"""Internal UI routing helpers."""

from __future__ import annotations

from typing import Any

import gradio as gr

ROUTE_AUTH = "auth"
ROUTE_STUDENT = "student"
ROUTE_TEACHER = "teacher"
ROUTE_AB_COMPARE = "ab_compare"
ROUTE_CHAT = "chat"
ROUTE_ADMIN = "admin"
ROUTE_TEACHER_COURSE = "teacher_course"
ROUTE_STUDENT_COURSE = "student_course"

_VALID_ROUTES = {
    ROUTE_AUTH,
    ROUTE_STUDENT,
    ROUTE_TEACHER,
    ROUTE_AB_COMPARE,
    ROUTE_CHAT,
    ROUTE_ADMIN,
    ROUTE_TEACHER_COURSE,
    ROUTE_STUDENT_COURSE,
}


def normalise_route(route: str | None) -> str:
    if route in _VALID_ROUTES:
        return route
    return ROUTE_AUTH


def route_visibility_updates(route: str | None) -> tuple[Any, Any, Any, Any, Any, Any, Any, Any]:
    current_route = normalise_route(route)
    return (
        gr.update(visible=current_route == ROUTE_AUTH),
        gr.update(visible=current_route == ROUTE_STUDENT),
        gr.update(visible=current_route == ROUTE_TEACHER),
        gr.update(visible=current_route == ROUTE_AB_COMPARE),
        gr.update(visible=current_route == ROUTE_CHAT),
        gr.update(visible=current_route == ROUTE_ADMIN),
        gr.update(visible=current_route == ROUTE_TEACHER_COURSE),
        gr.update(visible=current_route == ROUTE_STUDENT_COURSE),
    )
