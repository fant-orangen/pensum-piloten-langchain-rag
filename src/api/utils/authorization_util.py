"""Authorization helpers for API role and enrollment checks."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User


def require_teacher_or_admin(user: User) -> None:
    """Raise 403 unless the user holds a platform-level teacher or admin role."""
    if user.global_role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can perform this action.",
        )


def require_admin(user: User) -> None:
    """Raise 403 unless the user is an admin."""
    if user.global_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action.",
        )


def require_course_owner_or_admin(user: User, created_by_id: uuid.UUID) -> None:
    """Raise 403 unless the user created the course or is an admin."""
    if user.global_role == "admin":
        return

    if user.global_role != "teacher" or user.id != created_by_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creating teacher or an admin can perform this action.",
        )


async def require_course_teacher_or_admin(
    user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Raise 403 unless the user is enrolled as a teacher in the course or is an admin."""
    if user.global_role == "admin":
        return

    if user.global_role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a teacher of this course or an admin can perform this action.",
        )

    result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user.id,
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.role == "teacher",
        )
    )
    if result.scalars().first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a teacher of this course or an admin can perform this action.",
        )


async def require_unenroll_permission(
    current_user: User,
    target_enrollment: CourseEnrollment,
    course: Course,
    db: AsyncSession,
) -> None:
    """Raise 403 if the current user is not permitted to remove the target from the course.

    - Removing a student requires being a teacher of the course or an admin.
    - Removing a teacher requires being the course creator or an admin.
    """
    if current_user.global_role == "admin":
        return

    if target_enrollment.role == "teacher":
        require_course_owner_or_admin(current_user, course.created_by_id)
    else:
        await require_course_teacher_or_admin(current_user, course.id, db)
