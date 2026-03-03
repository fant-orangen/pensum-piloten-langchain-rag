"""JSON-backed course persistence."""

from __future__ import annotations

import json
from pathlib import Path

from src.domain import Course

COURSES_PATH = Path("data/courses.json")


def _normalise_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    items: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        cleaned_item = item.strip()
        if not cleaned_item or cleaned_item in seen:
            continue
        items.append(cleaned_item)
        seen.add(cleaned_item)
    return items


def load_courses() -> dict[str, Course]:
    if not COURSES_PATH.exists():
        return {}

    try:
        payload = json.loads(COURSES_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(payload, dict):
        return {}

    courses: dict[str, Course] = {}
    for course_key, course_data in payload.items():
        if not isinstance(course_key, str) or not isinstance(course_data, dict):
            continue

        course_id = course_data.get("course_id")
        name = course_data.get("name")
        created_at = course_data.get("created_at")
        responsible_teacher_username = course_data.get("responsible_teacher_username")
        if (
            not isinstance(course_id, str)
            or not course_id
            or not isinstance(name, str)
            or not name.strip()
            or not isinstance(created_at, str)
            or not created_at
            or not isinstance(responsible_teacher_username, str)
            or not responsible_teacher_username.strip()
        ):
            continue

        teacher_usernames = _normalise_string_list(course_data.get("teacher_usernames"))
        student_usernames = _normalise_string_list(course_data.get("student_usernames"))
        responsible_username = responsible_teacher_username.strip()
        if responsible_username not in teacher_usernames:
            teacher_usernames.insert(0, responsible_username)

        courses[course_key] = Course(
            course_id=course_id,
            name=name.strip(),
            created_at=created_at,
            responsible_teacher_username=responsible_username,
            teacher_usernames=teacher_usernames,
            student_usernames=student_usernames,
        )
    return courses


def save_courses(courses: dict[str, Course]) -> None:
    COURSES_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        course_id: {
            "course_id": course.course_id,
            "name": course.name,
            "created_at": course.created_at,
            "responsible_teacher_username": course.responsible_teacher_username,
            "teacher_usernames": list(course.teacher_usernames),
            "student_usernames": list(course.student_usernames),
        }
        for course_id, course in courses.items()
    }
    temp_path = COURSES_PATH.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temp_path.replace(COURSES_PATH)
