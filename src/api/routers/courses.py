"""Course endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization import (
    require_course_owner_or_admin,
    require_course_teacher_or_admin,
    require_teacher_or_admin,
)
from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.schemas.course import CourseCreate, CourseRead, EnrollmentCreate, EnrollmentRead

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


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Create a new course.

    Only users with a platform-level teacher or superadmin role may create courses.
    The creating user is automatically enrolled as a teacher of the new course.
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
    return CourseRead.model_validate(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a course.

    Only the teacher who created the course or a superadmin may delete it.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    require_course_owner_or_admin(current_user, course.created_by_id)

    await db.delete(course)
    await db.commit()


@router.post(
    "/{course_id}/enrollments",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_user(
    course_id: uuid.UUID,
    body: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentRead:
    """Enroll a user in a course by email.

    Only a teacher enrolled in the course or a superadmin may add users.
    The role field defaults to 'student' but can be set to 'teacher'.
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
    return EnrollmentRead.model_validate(enrollment)
