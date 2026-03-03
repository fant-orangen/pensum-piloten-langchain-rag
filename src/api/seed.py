"""Test data seeding.

Activated by setting SEED_TEST_DATA=true in the environment or .env file.
Inserts a teacher, a student, a course backed by the configured ChromaDB
collection, and enrolls the student in that course.

The seed is idempotent — each object is skipped if it already exists,
so the function is safe to call on every startup.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation  # noqa: F401 — keep metadata complete
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.services.auth import hash_password
from src.config import get_settings

logger = structlog.get_logger(__name__)

_TEACHER_EMAIL = "teacher@test.com"
_STUDENT_EMAIL = "student@test.com"
_COURSE_CODE = "TEST101"


async def seed(db: AsyncSession) -> None:
    settings = get_settings()

    # --- Teacher ---
    teacher = await _get_or_create_user(
        db,
        email=_TEACHER_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Teacher",
        global_role="teacher",
    )

    # --- Student ---
    student = await _get_or_create_user(
        db,
        email=_STUDENT_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Student",
        global_role="student",
    )

    # --- Course ---
    course_result = await db.execute(select(Course).where(Course.code == _COURSE_CODE))
    course = course_result.scalars().first()
    if course is None:
        course = Course(
            name="Test Course",
            code=_COURSE_CODE,
            chroma_collection=settings.chroma_collection_name,
            documents_dir=settings.documents_dir,
            rag_mode="kg_rag",
            created_by_id=teacher.id,
        )
        db.add(course)
        await db.flush()  # populate course.id before using it below
        logger.info("seed_created_course", code=_COURSE_CODE)
    else:
        logger.info("seed_course_exists", code=_COURSE_CODE)

    # --- Enrollment ---
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == student.id,
            CourseEnrollment.course_id == course.id,
        )
    )
    if enrollment_result.scalars().first() is None:
        db.add(CourseEnrollment(user_id=student.id, course_id=course.id, role="student"))
        logger.info("seed_enrolled_student", email=_STUDENT_EMAIL, course=_COURSE_CODE)

    teacher_enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == teacher.id,
            CourseEnrollment.course_id == course.id,
        )
    )
    if teacher_enrollment_result.scalars().first() is None:
        db.add(CourseEnrollment(user_id=teacher.id, course_id=course.id, role="teacher"))
        logger.info("seed_enrolled_teacher", email=_TEACHER_EMAIL, course=_COURSE_CODE)

    await db.commit()
    logger.info("seed_complete")


async def _get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    global_role: str,
) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            global_role=global_role,
        )
        db.add(user)
        await db.flush()  # populate user.id before referencing it
        logger.info("seed_created_user", email=email, role=global_role)
    else:
        logger.info("seed_user_exists", email=email)
    return user
