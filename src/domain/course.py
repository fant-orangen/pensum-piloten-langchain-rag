"""Course domain model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Course:
    course_id: str
    name: str
    created_at: str
    responsible_teacher_username: str
    teacher_usernames: list[str]
    student_usernames: list[str]
