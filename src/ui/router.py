"""Internal UI routing helpers."""

from __future__ import annotations

from typing import Any

import gradio as gr

ROUTE_AUTH = "auth"
ROUTE_STUDENT = "student"
ROUTE_AB_COMPARE = "ab_compare"

_VALID_ROUTES = {ROUTE_AUTH, ROUTE_STUDENT, ROUTE_AB_COMPARE}


def normalise_route(route: str | None) -> str:
    if route in _VALID_ROUTES:
        return route
    return ROUTE_AUTH


def route_visibility_updates(route: str | None) -> tuple[Any, Any, Any]:
    current_route = normalise_route(route)
    return (
        gr.update(visible=current_route == ROUTE_AUTH),
        gr.update(visible=current_route == ROUTE_STUDENT),
        gr.update(visible=current_route == ROUTE_AB_COMPARE),
    )
