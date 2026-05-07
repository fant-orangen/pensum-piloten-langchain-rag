"""Unit tests for safe single-course summary access."""

import uuid

import pytest
from fastapi import HTTPException

from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.services.courses import get_course_summary_for_user


class _ScalarResult:
    def __init__(self, first: object | None) -> None:
        self._first = first

    def first(self) -> object | None:
        return self._first


class _ExecuteResult:
    def __init__(self, first: object | None) -> None:
        self._scalars = _ScalarResult(first)

    def scalars(self) -> _ScalarResult:
        return self._scalars


class _FakeSession:
    def __init__(self, *results: object | None) -> None:
        self._results = list(results)
        self.execute_count = 0

    async def execute(self, _statement: object) -> _ExecuteResult:
        self.execute_count += 1
        return _ExecuteResult(self._results.pop(0))


def _user(*, role: str = "student") -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@test.com",
        hashed_password="hash",
        first_name="Test",
        last_name="User",
        global_role=role,
    )


def _course() -> Course:
    return Course(
        id=uuid.uuid4(),
        name="Algorithms",
        code="TDT9999",
        documents_dir="docs/TDT9999",
        course_specific_instructions="Teacher-only guidance",
        chroma_collection="internal_scope",
        created_by_id=uuid.uuid4(),
    )


@pytest.mark.asyncio
async def test_get_course_summary_for_user_returns_course_for_enrolled_user() -> None:
    user = _user()
    course = _course()
    enrollment = CourseEnrollment(user_id=user.id, course_id=course.id, role="student")
    db = _FakeSession(course, enrollment)

    result = await get_course_summary_for_user(user, course.id, db)

    assert result is course
    assert db.execute_count == 2


@pytest.mark.asyncio
async def test_get_course_summary_for_user_allows_admin_without_enrollment() -> None:
    admin = _user(role="admin")
    course = _course()
    db = _FakeSession(course)

    result = await get_course_summary_for_user(admin, course.id, db)

    assert result is course
    assert db.execute_count == 1


@pytest.mark.asyncio
async def test_get_course_summary_for_user_rejects_unenrolled_user() -> None:
    user = _user()
    course = _course()
    db = _FakeSession(course, None)

    with pytest.raises(HTTPException) as exc_info:
        await get_course_summary_for_user(user, course.id, db)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_course_summary_for_user_rejects_missing_course() -> None:
    user = _user()
    db = _FakeSession(None)

    with pytest.raises(HTTPException) as exc_info:
        await get_course_summary_for_user(user, uuid.uuid4(), db)

    assert exc_info.value.status_code == 404
