"""Course endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.course import (
    CourseCreate,
    CourseIngestionJobRead,
    CourseIngestionStartRequest,
    CourseMaterialRead,
    CourseRead,
    EnrollmentCreate,
    EnrollmentRead,
    EnrollmentWithUserRead,
)
from src.api.services.courses import (
    create_course,
    create_course_ingestion_job,
    delete_course,
    delete_course_material,
    enroll_user,
    get_course_enrollments,
    get_available_courses,
    get_enrolled_courses,
    list_course_materials,
    list_course_ingestion_jobs,
    get_responsible_courses,
    get_course_ingestion_job,
    unenroll_user,
    upload_course_material,
)
from src.api.services.ingestion_jobs import execute_course_ingestion_job

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


@router.get("/{course_id}/enrollments", response_model=list[EnrollmentWithUserRead])
async def list_enrollments(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EnrollmentWithUserRead]:
    """Return all enrollments in a course with basic user details."""
    rows = await get_course_enrollments(current_user, course_id, db)
    return [
        EnrollmentWithUserRead(
            user_id=enrollment.user_id,
            course_id=enrollment.course_id,
            role=enrollment.role,
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        )
        for enrollment, user in rows
    ]


@router.post(
    "/{course_id}/materials",
    response_model=CourseMaterialRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_course_material(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialRead:
    """Upload one material file for a course."""
    content = await file.read()
    material = await upload_course_material(
        current_user,
        course_id,
        filename=file.filename or "",
        content=content,
        mime_type=file.content_type,
        db=db,
    )
    return CourseMaterialRead.model_validate(material)


@router.get("/{course_id}/materials", response_model=list[CourseMaterialRead])
async def get_course_materials(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseMaterialRead]:
    """Return all uploaded materials for a course."""
    materials = await list_course_materials(current_user, course_id, db)
    return [CourseMaterialRead.model_validate(item) for item in materials]


@router.delete("/{course_id}/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course_material(
    course_id: uuid.UUID,
    material_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete one uploaded material from a course."""
    await delete_course_material(current_user, course_id, material_id, db)


@router.post(
    "/{course_id}/ingestions",
    response_model=CourseIngestionJobRead,
    status_code=status.HTTP_201_CREATED,
)
async def start_course_ingestion(
    course_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    body: CourseIngestionStartRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseIngestionJobRead:
    """Create a queued ingestion job for a course."""
    material_ids = body.material_ids if body is not None else None
    job, _selected_material_ids = await create_course_ingestion_job(
        current_user,
        course_id,
        db,
        material_ids=material_ids,
    )
    background_tasks.add_task(execute_course_ingestion_job, job.id)
    return CourseIngestionJobRead.model_validate(job)


@router.get("/{course_id}/ingestions", response_model=list[CourseIngestionJobRead])
async def get_course_ingestions(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseIngestionJobRead]:
    """Return ingestion jobs for a course."""
    jobs = await list_course_ingestion_jobs(current_user, course_id, db)
    return [CourseIngestionJobRead.model_validate(job) for job in jobs]


@router.get("/{course_id}/ingestions/{job_id}", response_model=CourseIngestionJobRead)
async def get_course_ingestion(
    course_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseIngestionJobRead:
    """Return one ingestion job for a course."""
    job = await get_course_ingestion_job(current_user, course_id, job_id, db)
    return CourseIngestionJobRead.model_validate(job)


@router.delete("/{course_id}/enrollments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enrollment(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a user from a course."""
    await unenroll_user(current_user, course_id, user_id, db)
