"""Application services."""

from src.services.auth_service import (
    ensure_admin_user,
    hash_password,
    login_user,
    logout_user,
    register_user,
    upgrade_user_to_teacher,
    verify_password,
)
from src.services.course_service import (
    add_student_to_course,
    create_course,
    get_addable_students_for_course,
    get_course,
    get_student_courses,
    get_teacher_available_courses,
    get_teacher_responsible_courses,
    list_students_in_course,
)

__all__ = [
    "add_student_to_course",
    "create_course",
    "ensure_admin_user",
    "get_addable_students_for_course",
    "get_course",
    "get_student_courses",
    "get_teacher_available_courses",
    "get_teacher_responsible_courses",
    "hash_password",
    "list_students_in_course",
    "login_user",
    "logout_user",
    "register_user",
    "upgrade_user_to_teacher",
    "verify_password",
]
