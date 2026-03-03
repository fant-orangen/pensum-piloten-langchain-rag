"""Course endpoints."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.course import CourseCreate, CourseRead, EnrollmentCreate, EnrollmentRead
from src.api.services.courses import (
    create_course,
    delete_course,
    enroll_user,
    get_available_courses,
    get_enrolled_courses,
    get_responsible_courses,
    unenroll_user,
)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead])
async def list_my_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses the authenticated user is enrolled in."""
    courses = await get_enrolled_courses(current_user.id, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/available", response_model=list[CourseRead])
async def list_available_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses the authenticated user is enrolled in (any role)."""
    courses = await get_available_courses(current_user.id, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/responsible", response_model=list[CourseRead])
async def list_responsible_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses where the authenticated user is enrolled as a teacher."""
    courses = await get_responsible_courses(current_user.id, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def new_course(
    body: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Create a new course."""
    course = await create_course(current_user, body, db)
    return CourseRead.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a course."""
    await delete_course(current_user, course_id, db)


@router.post(
    "/{course_id}/enrollments",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_enrollment(
    course_id: uuid.UUID,
    body: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentRead:
    """Enroll a user in a course by email."""
    enrollment = await enroll_user(current_user, course_id, body, db)
    return EnrollmentRead.model_validate(enrollment)


@router.delete("/{course_id}/enrollments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enrollment(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a user from a course."""
    await unenroll_user(current_user, course_id, user_id, db)
