"""Course services."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from src.domain import Course
from src.storage import load_courses, load_users, save_courses


def _sorted_courses(courses: list[Course]) -> list[Course]:
    return sorted(courses, key=lambda course: (course.name.lower(), course.created_at, course.course_id))


def get_course(course_id: str) -> Course | None:
    cleaned_course_id = course_id.strip()
    if not cleaned_course_id:
        return None

    courses = load_courses()
    return courses.get(cleaned_course_id)


def _can_manage_course(course: Course, actor_username: str) -> bool:
    cleaned_actor_username = actor_username.strip()
    if not cleaned_actor_username:
        return False

    if cleaned_actor_username == course.responsible_teacher_username:
        return True
    if cleaned_actor_username in course.teacher_usernames:
        return True

    users = load_users()
    actor = users.get(cleaned_actor_username)
    return actor is not None and actor.role == "admin"


def create_course(teacher_username: str, course_name: str) -> tuple[bool, str, Course | None]:
    cleaned_teacher_username = teacher_username.strip()
    cleaned_course_name = course_name.strip()
    if not cleaned_teacher_username or not cleaned_course_name:
        return False, "Fyll ut alle feltene.", None

    course = Course(
        course_id=uuid4().hex,
        name=cleaned_course_name,
        created_at=datetime.now(timezone.utc).isoformat(),
        responsible_teacher_username=cleaned_teacher_username,
        teacher_usernames=[cleaned_teacher_username],
        student_usernames=[],
    )
    courses = load_courses()
    courses[course.course_id] = course
    save_courses(courses)
    return True, "Faget ble opprettet.", course


def get_teacher_responsible_courses(teacher_username: str) -> list[Course]:
    cleaned_teacher_username = teacher_username.strip()
    if not cleaned_teacher_username:
        return []

    courses = load_courses()
    matches = [
        course
        for course in courses.values()
        if course.responsible_teacher_username == cleaned_teacher_username
    ]
    return _sorted_courses(matches)


def get_teacher_available_courses(teacher_username: str) -> list[Course]:
    cleaned_teacher_username = teacher_username.strip()
    if not cleaned_teacher_username:
        return []

    courses = load_courses()
    matches = [
        course
        for course in courses.values()
        if course.responsible_teacher_username == cleaned_teacher_username
        or cleaned_teacher_username in course.teacher_usernames
    ]
    return _sorted_courses(matches)


def get_student_courses(student_username: str) -> list[Course]:
    cleaned_student_username = student_username.strip()
    if not cleaned_student_username:
        return []

    courses = load_courses()
    matches = [
        course
        for course in courses.values()
        if cleaned_student_username in course.student_usernames
    ]
    return _sorted_courses(matches)


def add_student_to_course(
    course_id: str,
    student_username: str,
    actor_username: str,
) -> tuple[bool, str]:
    cleaned_course_id = course_id.strip()
    cleaned_student_username = student_username.strip()
    cleaned_actor_username = actor_username.strip()
    if not cleaned_course_id or not cleaned_student_username or not cleaned_actor_username:
        return False, "Fyll ut alle feltene."

    courses = load_courses()
    course = courses.get(cleaned_course_id)
    if course is None:
        return False, "Fant ikke faget."
    if not _can_manage_course(course, cleaned_actor_username):
        return False, "Ikke tillatt."

    users = load_users()
    student = users.get(cleaned_student_username)
    if student is None or student.role != "student":
        return False, "Fant ikke studenten."
    if cleaned_student_username in course.student_usernames:
        return False, "Studenten er allerede lagt til."

    updated_students = list(course.student_usernames)
    updated_students.append(cleaned_student_username)
    courses[cleaned_course_id] = Course(
        course_id=course.course_id,
        name=course.name,
        created_at=course.created_at,
        responsible_teacher_username=course.responsible_teacher_username,
        teacher_usernames=list(course.teacher_usernames),
        student_usernames=updated_students,
    )
    save_courses(courses)
    return True, "Student lagt til i faget."


def list_students_in_course(course_id: str) -> list[str]:
    course = get_course(course_id)
    if course is None:
        return []
    return list(course.student_usernames)


def get_addable_students_for_course(course_id: str, actor_username: str) -> list[tuple[str, str]]:
    cleaned_course_id = course_id.strip()
    cleaned_actor_username = actor_username.strip()
    if not cleaned_course_id or not cleaned_actor_username:
        return []

    course = get_course(cleaned_course_id)
    if course is None or not _can_manage_course(course, cleaned_actor_username):
        return []

    users = load_users()
    choices: list[tuple[str, str]] = []
    for username in sorted(users):
        user = users[username]
        if user.role != "student":
            continue
        if username in course.student_usernames:
            continue
        full_name = user.name or username
        choices.append((f"{username} - {full_name}", username))
    return choices
