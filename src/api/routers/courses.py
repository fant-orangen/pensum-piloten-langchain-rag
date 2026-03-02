"""Course endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    Only users with global_role 'teacher' or 'superadmin' may create courses.
    The creating user is automatically enrolled as a teacher of the course.
    """
    if current_user.global_role not in ("teacher", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and superadmins can create courses.",
        )

    # Reject duplicate course codes.
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
    await db.flush()  # Populate course.id before creating the enrollment.

    # Enroll the creating teacher in the course with role "teacher".
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

    is_creator = course.created_by_id == current_user.id
    if current_user.global_role != "superadmin" and not is_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creating teacher or a superadmin can delete this course.",
        )

    await db.delete(course)
    await db.commit()


@router.post(
    "/{course_id}/enrollments",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    course_id: uuid.UUID,
    body: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentRead:
    """Enroll a user in a course by email.

    Only a teacher enrolled in the course or a superadmin may add students.
    The role defaults to 'student' but can be set to 'teacher'.
    """
    # Verify the course exists.
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    # Authorise: superadmin always allowed; otherwise the requester must be a
    # teacher enrolled in this course.
    if current_user.global_role != "superadmin":
        auth_result = await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.user_id == current_user.id,
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.role == "teacher",
            )
        )
        if auth_result.scalars().first() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only a teacher of this course or a superadmin can enroll users.",
            )

    # Look up the target user by email.
    user_result = await db.execute(select(User).where(User.email == body.user_email))
    target_user = user_result.scalars().first()
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user with email '{body.user_email}' found.",
        )

    # Prevent duplicate enrollments.
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
