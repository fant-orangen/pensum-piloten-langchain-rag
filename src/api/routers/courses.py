"""Course endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.course import (
    CourseCreate,
    CourseDocumentRead,
    CourseInstructionsUpdate,
    CourseMaterialsStatusRead,
    CourseRead,
    EnrollmentCreate,
    EnrollmentRead,
)
from src.api.services.course_documents import (
    get_course_materials_status,
    list_course_documents,
    queue_course_material_rebuild,
    run_course_material_rebuild,
    stage_course_document_removal,
    stage_course_documents,
)
from src.api.services.courses import (
    create_course,
    delete_course,
    enroll_user,
    get_available_courses,
    get_enrolled_courses,
    get_responsible_courses,
    unenroll_user,
    update_course_specific_instructions,
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


@router.get("/{course_id}/documents", response_model=list[CourseDocumentRead])
async def list_documents(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseDocumentRead]:
    """List staged and active source materials for a course."""
    documents = await list_course_documents(current_user, course_id, db)
    return [CourseDocumentRead.model_validate(document) for document in documents]


@router.post(
    "/{course_id}/documents",
    response_model=list[CourseDocumentRead],
    status_code=status.HTTP_201_CREATED,
)
async def add_documents(
    course_id: uuid.UUID,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseDocumentRead]:
    """Stage new source materials for a course."""
    documents = await stage_course_documents(current_user, course_id, files, db)
    return [CourseDocumentRead.model_validate(document) for document in documents]


@router.delete("/{course_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(
    course_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Stage removal of a source document from a course."""
    await stage_course_document_removal(current_user, course_id, document_id, db)


@router.get("/{course_id}/documents/status", response_model=CourseMaterialsStatusRead)
async def get_documents_status(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialsStatusRead:
    """Return current rebuild state and pending document counts for a course."""
    return await get_course_materials_status(current_user, course_id, db)


@router.post(
    "/{course_id}/documents/confirm",
    response_model=CourseMaterialsStatusRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def confirm_document_changes(
    course_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialsStatusRead:
    """Confirm all staged add/remove changes and start a versioned rebuild."""
    course_status = await queue_course_material_rebuild(current_user, course_id, db)
    background_tasks.add_task(run_course_material_rebuild, course_id)
    return course_status


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a course."""
    await delete_course(current_user, course_id, db)


@router.patch("/{course_id}/instructions", response_model=CourseRead)
async def update_course_instructions(
    course_id: uuid.UUID,
    body: CourseInstructionsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Update the course-specific prompt instructions for a course."""
    course = await update_course_specific_instructions(current_user, course_id, body, db)
    return CourseRead.model_validate(course)


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
