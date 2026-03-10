"""UI API service layer — thin wrappers around the FastAPI backend."""

from src.ui.services.auth_service import login, register
from src.ui.services.admin_service import list_users, promote_user_to_teacher
from src.ui.services.course_service import (
    create_course,
    delete_course,
    enroll_user,
    list_courses,
    unenroll_user,
)
from src.ui.services.conversation_service import (
    create_conversation,
    get_messages,
    list_conversations,
    send_message,
)

__all__ = [
    "create_conversation",
    "create_course",
    "delete_course",
    "enroll_user",
    "get_messages",
    "list_users",
    "list_conversations",
    "list_courses",
    "login",
    "promote_user_to_teacher",
    "register",
    "send_message",
    "unenroll_user",
]
