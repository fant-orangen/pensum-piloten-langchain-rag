import io
import uuid

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from starlette.datastructures import UploadFile

from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.enrollment_import_preview import EnrollmentImportPreview
from src.api.models.user import User
from src.api.services.courses import (
    cancel_enrollment_import,
    confirm_enrollment_import,
    get_course_specific_instructions,
    preview_enrollment_import,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: SQLModel.metadata.create_all(
                sync_conn,
                tables=[
                    User.__table__,
                    Course.__table__,
                    CourseEnrollment.__table__,
                    EnrollmentImportPreview.__table__,
                ],
            )
        )

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def seeded_course(db_session: AsyncSession) -> dict[str, object]:
    teacher = User(
        email="teacher@test.com",
        hashed_password="hash",
        first_name="Teach",
        last_name="Er",
        global_role="teacher",
    )
    second_teacher = User(
        email="other-teacher@test.com",
        hashed_password="hash",
        first_name="Other",
        last_name="Teacher",
        global_role="teacher",
    )
    enrollable_student = User(
        email="Existing.Student@Test.com",
        hashed_password="hash",
        first_name="Enrollable",
        last_name="Student",
    )
    already_enrolled_student = User(
        email="already@student.com",
        hashed_password="hash",
        first_name="Already",
        last_name="Enrolled",
    )
    course = Course(
        name="Algorithms",
        code="TDT9999",
        documents_dir="docs/TDT9999",
        course_specific_instructions="Use Socratic questioning.",
        created_by_id=teacher.id,
    )
    outsider_teacher = User(
        email="outsider-teacher@test.com",
        hashed_password="hash",
        first_name="Out",
        last_name="Sider",
        global_role="teacher",
    )

    db_session.add_all(
        [
            teacher,
            second_teacher,
            enrollable_student,
            already_enrolled_student,
            outsider_teacher,
            course,
        ]
    )
    await db_session.flush()

    db_session.add(CourseEnrollment(user_id=teacher.id, course_id=course.id, role="teacher"))
    db_session.add(CourseEnrollment(user_id=second_teacher.id, course_id=course.id, role="teacher"))
    db_session.add(
        CourseEnrollment(
            user_id=already_enrolled_student.id,
            course_id=course.id,
            role="student",
        )
    )
    await db_session.commit()

    return {
        "teacher": teacher,
        "second_teacher": second_teacher,
        "outsider_teacher": outsider_teacher,
        "enrollable_student": enrollable_student,
        "already_enrolled_student": already_enrolled_student,
        "course": course,
    }


def _build_upload(content: str) -> UploadFile:
    return UploadFile(filename="students.csv", file=io.BytesIO(content.encode("utf-8")))


@pytest.mark.asyncio
async def test_preview_enrollment_import_returns_classification_and_stores_preview(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    teacher = seeded_course["teacher"]
    course = seeded_course["course"]

    preview = await preview_enrollment_import(
        teacher,
        course.id,
        _build_upload(
            "\n".join(
                [
                    "email",
                    "existing.student@test.com",
                    "missing@student.com",
                    "already@student.com",
                    "not-an-email",
                    "existing.student@test.com",
                ]
            )
        ),
        db_session,
    )

    assert preview.enrollable_emails == ["existing.student@test.com"]
    assert len(preview.missing_candidates) == 1
    assert preview.missing_candidates[0].email == "missing@student.com"
    assert preview.already_enrolled_emails == ["already@student.com"]
    assert preview.duplicate_emails == ["existing.student@test.com"]
    assert preview.invalid_emails == ["not-an-email"]
    assert preview.has_warnings is True

    previews = (
        await db_session.execute(select(EnrollmentImportPreview).where(EnrollmentImportPreview.id == preview.preview_id))
    ).scalars().all()
    assert len(previews) == 1
    assert previews[0].candidate_emails == [
        "existing.student@test.com",
        "missing@student.com",
        "already@student.com",
    ]


@pytest.mark.asyncio
async def test_confirm_enrollment_import_enrolls_students_and_deletes_preview(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    teacher = seeded_course["teacher"]
    course = seeded_course["course"]
    enrollable_student = seeded_course["enrollable_student"]

    preview = await preview_enrollment_import(
        teacher,
        course.id,
        _build_upload(
            "\n".join(
                [
                    "existing.student@test.com",
                    "missing@student.com",
                    "already@student.com",
                ]
            )
        ),
        db_session,
    )

    confirmation = await confirm_enrollment_import(
        teacher,
        course.id,
        preview.preview_id,
        db_session,
    )

    assert "existing.student@test.com" in confirmation.enrolled_emails
    assert "missing@student.com" in confirmation.enrolled_emails
    assert confirmation.created_emails == ["missing@student.com"]
    assert confirmation.already_enrolled_emails == ["already@student.com"]

    enrollment = (
        await db_session.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.user_id == enrollable_student.id,
            )
        )
    ).scalars().first()
    assert enrollment is not None
    assert enrollment.role == "student"

    # Verify the new account was created and enrolled.
    created_user = (
        await db_session.execute(select(User).where(User.email == "missing@student.com"))
    ).scalars().first()
    assert created_user is not None
    new_enrollment = (
        await db_session.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.course_id == course.id,
                CourseEnrollment.user_id == created_user.id,
            )
        )
    ).scalars().first()
    assert new_enrollment is not None
    assert new_enrollment.role == "student"

    stored_preview = (
        await db_session.execute(
            select(EnrollmentImportPreview).where(EnrollmentImportPreview.id == preview.preview_id)
        )
    ).scalars().first()
    assert stored_preview is None


@pytest.mark.asyncio
async def test_cancel_enrollment_import_deletes_preview(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    teacher = seeded_course["teacher"]
    course = seeded_course["course"]

    preview = await preview_enrollment_import(
        teacher,
        course.id,
        _build_upload("existing.student@test.com"),
        db_session,
    )

    await cancel_enrollment_import(teacher, course.id, preview.preview_id, db_session)

    stored_preview = (
        await db_session.execute(
            select(EnrollmentImportPreview).where(EnrollmentImportPreview.id == preview.preview_id)
        )
    ).scalars().first()
    assert stored_preview is None


@pytest.mark.asyncio
async def test_confirm_creates_account_with_name_from_csv(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    teacher = seeded_course["teacher"]
    course = seeded_course["course"]

    preview = await preview_enrollment_import(
        teacher,
        course.id,
        _build_upload("email,first name,last name\nnew@student.com,Alice,Smith"),
        db_session,
    )

    assert len(preview.missing_candidates) == 1
    assert preview.missing_candidates[0].first_name == "Alice"
    assert preview.missing_candidates[0].last_name == "Smith"

    confirmation = await confirm_enrollment_import(
        teacher,
        course.id,
        preview.preview_id,
        db_session,
    )

    assert confirmation.created_emails == ["new@student.com"]

    created_user = (
        await db_session.execute(select(User).where(User.email == "new@student.com"))
    ).scalars().first()
    assert created_user is not None
    assert created_user.first_name == "Alice"
    assert created_user.last_name == "Smith"


@pytest.mark.asyncio
async def test_get_course_specific_instructions_returns_current_value_for_teacher(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    teacher = seeded_course["teacher"]
    course = seeded_course["course"]

    result = await get_course_specific_instructions(teacher, course.id, db_session)

    assert result.course_id == course.id
    assert result.course_specific_instructions == "Use Socratic questioning."


@pytest.mark.asyncio
async def test_get_course_specific_instructions_rejects_teacher_not_in_course(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    outsider_teacher = seeded_course["outsider_teacher"]
    course = seeded_course["course"]

    with pytest.raises(HTTPException) as exc_info:
        await get_course_specific_instructions(outsider_teacher, course.id, db_session)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_course_specific_instructions_rejects_missing_course(
    db_session: AsyncSession,
    seeded_course: dict[str, object],
) -> None:
    teacher = seeded_course["teacher"]

    with pytest.raises(HTTPException) as exc_info:
        await get_course_specific_instructions(teacher, uuid.uuid4(), db_session)

    assert exc_info.value.status_code == 404
