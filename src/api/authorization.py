"""Authorization helpers — role and enrollment checks.

Each function raises HTTP 403 when the requirement is not met, so callers
can use them as plain assertions without any extra branching.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User


def require_teacher_or_admin(user: User) -> None:
    """Raise 403 unless the user holds a platform-level teacher or superadmin role."""
    if user.global_role not in ("teacher", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and superadmins can perform this action.",
        )


def require_admin(user: User) -> None:
    """Raise 403 unless the user is a superadmin."""
    if user.global_role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can perform this action.",
        )


def require_course_owner_or_admin(user: User, created_by_id: uuid.UUID) -> None:
    """Raise 403 unless the user created the course or is a superadmin."""
    if user.global_role != "superadmin" and user.id != created_by_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creating teacher or a superadmin can perform this action.",
        )


async def require_course_teacher_or_admin(
    user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Raise 403 unless the user is enrolled as a teacher in the course or is a superadmin."""
    if user.global_role == "superadmin":
        return

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
            detail="Only a teacher of this course or a superadmin can perform this action.",
        )
