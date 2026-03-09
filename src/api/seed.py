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
_ADMIN_EMAIL = "admin@test.com"
_COURSE_CODE = "TEST101"
_SECOND_COURSE_CODE = "TEST102"
_COURSE_SPECIFIC_INSTRUCTIONS = (
    "This course is specifically about understanding NTFS when discussing file systems. "
    "When file-system concepts are explained, always describe them with reference to NTFS."
)


async def seed(db: AsyncSession) -> None:
    settings = get_settings()

    # --- Admin ---
    admin = await _get_or_create_user(
        db,
        email=_ADMIN_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Admin",
        global_role="admin",
    )

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
            course_specific_instructions=_COURSE_SPECIFIC_INSTRUCTIONS,
            created_by_id=teacher.id,
        )
        db.add(course)
        await db.flush()  # populate course.id before using it below
        logger.info("seed_created_course", code=_COURSE_CODE)
    else:
        course.course_specific_instructions = _COURSE_SPECIFIC_INSTRUCTIONS
        db.add(course)
        logger.info("seed_course_exists", code=_COURSE_CODE)

    # --- Second Course ---
    second_course_result = await db.execute(select(Course).where(Course.code == _SECOND_COURSE_CODE))
    second_course = second_course_result.scalars().first()
    if second_course is None:
        second_course = Course(
            name="Second Test Course",
            code=_SECOND_COURSE_CODE,
            chroma_collection=settings.chroma_collection_name,
            documents_dir=settings.documents_dir,
            rag_mode="kg_rag",
            created_by_id=admin.id,
        )
        db.add(second_course)
        await db.flush()
        logger.info("seed_created_course", code=_SECOND_COURSE_CODE)
    else:
        second_course.chroma_collection = settings.chroma_collection_name
        db.add(second_course)
        logger.info("seed_course_exists", code=_SECOND_COURSE_CODE)

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

    second_course_teacher_enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == teacher.id,
            CourseEnrollment.course_id == second_course.id,
        )
    )
    second_course_teacher_enrollment = second_course_teacher_enrollment_result.scalars().first()
    if second_course_teacher_enrollment is None:
        db.add(CourseEnrollment(user_id=teacher.id, course_id=second_course.id, role="student"))
        logger.info("seed_enrolled_teacher", email=_TEACHER_EMAIL, course=_SECOND_COURSE_CODE, role="student")
    elif second_course_teacher_enrollment.role != "student":
        second_course_teacher_enrollment.role = "student"
        db.add(second_course_teacher_enrollment)
        logger.info(
            "seed_updated_teacher_enrollment",
            email=_TEACHER_EMAIL,
            course=_SECOND_COURSE_CODE,
            role="student",
        )

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
