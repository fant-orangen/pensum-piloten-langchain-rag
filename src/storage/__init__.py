"""Storage helpers."""

from src.storage.courses_repo import load_courses, save_courses
from src.storage.users_repo import load_users, save_users

__all__ = ["load_courses", "load_users", "save_courses", "save_users"]
