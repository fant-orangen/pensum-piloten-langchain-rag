"""Course business logic and database queries."""

import uuid
from pathlib import Path

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
from src.api.models.course_ingestion_job import CourseIngestionJob
from src.api.models.course_material import CourseMaterial
from src.api.models.user import User
from src.api.schemas.course import CourseCreate, EnrollmentCreate
from src.config import get_settings

_ACTIVE_INGESTION_STATUSES = ("queued", "running")


async def get_enrolled_courses(user_id: uuid.UUID, db: AsyncSession) -> list[Course]:
    """Return all courses the given user is enrolled in."""
    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(CourseEnrollment.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_available_courses(user_id: uuid.UUID, db: AsyncSession) -> list[Course]:
    """Return all courses the given user is enrolled in (any role)."""
    return await get_enrolled_courses(user_id, db)


async def get_responsible_courses(user_id: uuid.UUID, db: AsyncSession) -> list[Course]:
    """Return all courses where the given user is enrolled as a teacher."""
    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.role == "teacher",
        )
    )
    return list(result.scalars().all())


async def create_course(current_user: User, body: CourseCreate, db: AsyncSession) -> Course:
    """Create a new course and enroll the creating user as a teacher.

    Raises 403 if the user lacks the teacher or admin role.
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
    Raises 403 if the user is not the course creator or an admin.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    require_course_owner_or_admin(current_user, course.created_by_id)

    materials_result = await db.execute(select(CourseMaterial).where(CourseMaterial.course_id == course_id))
    materials = list(materials_result.scalars().all())
    for material in materials:
        try:
            path = Path(material.storage_path)
            if path.exists():
                path.unlink()
        except Exception:
            pass

    # Remove all enrollments first to avoid FK constraint violations.
    await db.execute(sa_delete(CourseEnrollment).where(CourseEnrollment.course_id == course_id))
    await db.execute(sa_delete(CourseMaterial).where(CourseMaterial.course_id == course_id))
    await db.execute(sa_delete(CourseIngestionJob).where(CourseIngestionJob.course_id == course_id))
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
    Raises 403 if the current user is not a teacher of the course or an admin.
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


async def get_course_enrollments(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> list[tuple[CourseEnrollment, User]]:
    """Return all enrollments for a course with basic user details.

    Raises 404 if the course does not exist.
    Raises 403 if the current user is not a teacher of the course or an admin.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    result = await db.execute(
        select(CourseEnrollment, User)
        .join(User, User.id == CourseEnrollment.user_id)
        .where(CourseEnrollment.course_id == course_id)
        .order_by(User.email)
    )
    return list(result.all())


async def upload_course_material(
    current_user: User,
    course_id: uuid.UUID,
    *,
    filename: str,
    content: bytes,
    mime_type: str | None,
    db: AsyncSession,
) -> CourseMaterial:
    """Store one uploaded file as course material.

    Raises 404 if the course does not exist.
    Raises 403 if the current user is not a teacher of the course or an admin.
    Raises 400 if the upload is empty or the filename is invalid.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    clean_name = Path(filename or "").name.strip()
    if not clean_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    settings = get_settings()
    materials_dir = Path(settings.course_materials_dir) / str(course_id)
    materials_dir.mkdir(parents=True, exist_ok=True)

    material_id = uuid.uuid4()
    suffix = Path(clean_name).suffix
    stored_path = materials_dir / f"{material_id}{suffix}"
    stored_path.write_bytes(content)

    material = CourseMaterial(
        id=material_id,
        course_id=course_id,
        uploaded_by_id=current_user.id,
        original_filename=clean_name,
        storage_path=str(stored_path),
        mime_type=mime_type or None,
        size_bytes=len(content),
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


async def list_course_materials(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> list[CourseMaterial]:
    """Return all materials for a course.

    Raises 404 if the course does not exist.
    Raises 403 if the current user is not a teacher of the course or an admin.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    result = await db.execute(
        select(CourseMaterial)
        .where(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_course_material(
    current_user: User,
    course_id: uuid.UUID,
    material_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete one course material and its stored file.

    Raises 404 if the course or material does not exist.
    Raises 403 if the current user is not a teacher of the course or an admin.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    material_result = await db.execute(
        select(CourseMaterial).where(
            CourseMaterial.id == material_id,
            CourseMaterial.course_id == course_id,
        )
    )
    material = material_result.scalars().first()
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found.")

    try:
        path = Path(material.storage_path)
        if path.exists():
            path.unlink()
    except Exception:
        # Best effort file cleanup; database state remains source of truth.
        pass

    await db.delete(material)
    await db.commit()


async def create_course_ingestion_job(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> CourseIngestionJob:
    """Create a queued ingestion job for a course.

    Raises 404 if the course does not exist.
    Raises 403 if the current user is not a teacher of the course or an admin.
    Raises 409 when there is already a queued/running job for the course.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    active_result = await db.execute(
        select(CourseIngestionJob).where(
            CourseIngestionJob.course_id == course_id,
            CourseIngestionJob.status.in_(_ACTIVE_INGESTION_STATUSES),
        )
    )
    if active_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingestion job is already running for this course.",
        )

    job = CourseIngestionJob(
        course_id=course_id,
        triggered_by_id=current_user.id,
        status="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def list_course_ingestion_jobs(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> list[CourseIngestionJob]:
    """List ingestion jobs for a course, newest first."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    result = await db.execute(
        select(CourseIngestionJob)
        .where(CourseIngestionJob.course_id == course_id)
        .order_by(CourseIngestionJob.created_at.desc())
    )
    return list(result.scalars().all())


async def get_course_ingestion_job(
    current_user: User,
    course_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession,
) -> CourseIngestionJob:
    """Return one ingestion job by ID for a course."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    result = await db.execute(
        select(CourseIngestionJob).where(
            CourseIngestionJob.id == job_id,
            CourseIngestionJob.course_id == course_id,
        )
    )
    job = result.scalars().first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingestion job not found.")
    return job
