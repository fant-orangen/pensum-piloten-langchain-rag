"""Course business logic and database queries."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization import (
    require_course_owner_or_admin,
    require_course_teacher_or_admin,
    require_teacher_or_admin,
    require_unenroll_permission,
)
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.schemas.course import CourseCreate, EnrollmentCreate


async def get_enrolled_courses(user_id: uuid.UUID, db: AsyncSession) -> list[Course]:
    """Return all courses the given user is enrolled in."""
    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(CourseEnrollment.user_id == user_id)
    )
    return list(result.scalars().all())


async def create_course(current_user: User, body: CourseCreate, db: AsyncSession) -> Course:
    """Create a new course and enroll the creating user as a teacher.

    Raises 403 if the user lacks the teacher or superadmin role.
    Raises 409 if the course code is already taken.
    """
    require_teacher_or_admin(current_user)

    existing = await db.execute(select(Course).where(Course.code == body.code))
    if existing.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A course with code '{body.code}' already exists.",
        )

    course = Course(
        name=body.name,
        code=body.code,
        chroma_collection=body.chroma_collection,
        documents_dir=body.documents_dir,
        description=body.description,
        rag_mode=body.rag_mode,
        created_by_id=current_user.id,
    )
    db.add(course)
    await db.flush()  # Populate course.id before the enrollment FK reference.

    enrollment = CourseEnrollment(
        user_id=current_user.id,
        course_id=course.id,
        role="teacher",
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(current_user: User, course_id: uuid.UUID, db: AsyncSession) -> None:
    """Delete a course.

    Raises 404 if the course does not exist.
    Raises 403 if the user is not the course creator or a superadmin.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    require_course_owner_or_admin(current_user, course.created_by_id)

    # Remove all enrollments first to avoid FK constraint violations.
    await db.execute(sa_delete(CourseEnrollment).where(CourseEnrollment.course_id == course_id))
    await db.delete(course)
    await db.commit()


async def enroll_user(
    current_user: User,
    course_id: uuid.UUID,
    body: EnrollmentCreate,
    db: AsyncSession,
) -> CourseEnrollment:
    """Enroll a user in a course by email.

    Raises 404 if the course or target user does not exist.
    Raises 403 if the current user is not a teacher of the course or a superadmin.
    Raises 409 if the target user is already enrolled.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    user_result = await db.execute(select(User).where(User.email == body.user_email))
    target_user = user_result.scalars().first()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user with email '{body.user_email}' found.",
        )

    dup_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == target_user.id,
            CourseEnrollment.course_id == course_id,
        )
    )
    if dup_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already enrolled in this course.",
        )

    enrollment = CourseEnrollment(
        user_id=target_user.id,
        course_id=course_id,
        role=body.role,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def unenroll_user(
    current_user: User,
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Remove a user from a course.

    Raises 404 if the course or enrollment does not exist.
    Raises 403 based on the target's role (see require_unenroll_permission).
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id,
        )
    )
    enrollment = enrollment_result.scalars().first()
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not enrolled in this course.",
        )

    await require_unenroll_permission(current_user, enrollment, course, db)

    await db.delete(enrollment)
    await db.commit()
