"""UI pages."""

from src.ui.pages.ab_page import AB_PAGE_CSS, build_ab_app, build_ab_page
from src.ui.pages.auth_page import build_auth_page, handle_login, handle_register
from src.ui.pages.chat_page import build_chat_page
from src.ui.pages.student_page import (
    build_student_page,
    handle_back_to_student,
    handle_logout,
    handle_open_ab_compare,
    handle_open_chat,
)

__all__ = [
    "AB_PAGE_CSS",
    "build_ab_app",
    "build_ab_page",
    "build_auth_page",
    "build_chat_page",
    "build_student_page",
    "handle_back_to_student",
    "handle_login",
    "handle_logout",
    "handle_open_ab_compare",
    "handle_open_chat",
    "handle_register",
]
