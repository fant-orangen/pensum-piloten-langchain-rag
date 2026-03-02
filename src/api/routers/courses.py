"""Course endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.schemas.course import CourseRead

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead])
async def list_my_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses the authenticated user is enrolled in."""
    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(CourseEnrollment.user_id == current_user.id)
    )
    return [CourseRead.model_validate(c) for c in result.scalars().all()]
