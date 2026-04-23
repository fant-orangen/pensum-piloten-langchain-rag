"""Course endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.course import (
    CourseCreate,
    CourseDocumentRead,
    CourseInstructionsRead,
    CourseInstructionsUpdate,
    EnrollmentImportConfirmRead,
    EnrollmentImportPreviewRead,
    CourseMaterialsStatusRead,
    CourseRead,
    CourseStudentRead,
    EnrollmentCreate,
    EnrollmentRead,
    ZipImportResultRead,
)
from src.api.schemas.pagination import Page, PaginationParams
from src.api.services.course_documents import (
    get_course_materials_status,
    list_course_documents,
    queue_course_material_rebuild,
    run_course_material_rebuild,
    stage_all_course_documents_removal,
    stage_course_document_removal,
    stage_course_documents,
    stage_course_documents_from_zip,
)
from src.api.services.courses import (
    advance_study_course,
    cancel_enrollment_import,
    confirm_enrollment_import,
    create_course,
    delete_course,
    enroll_user,
    get_course,
    get_course_specific_instructions,
    get_available_courses,
    get_course_students,
    get_enrolled_courses,
    preview_enrollment_import,
    get_responsible_courses,
    unenroll_all_students,
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
    """Return all courses where the authenticated user is enrolled as a student."""
    courses = await get_available_courses(current_user.id, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/responsible", response_model=list[CourseRead])
async def list_responsible_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses where the authenticated user is enrolled as a teacher."""
    courses = await get_responsible_courses(current_user, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.post("/advance", response_model=CourseRead)
async def advance_my_study_course(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Advance the caller to the next course in the os_g1 -> os_g2 -> os_g3 study cycle.

    Atomically unenrolls the caller from their current study course and enrolls
    them in the next one as a student. Defined before `/{course_id}` so the
    literal `"advance"` path is not treated as a UUID.
    """
    course = await advance_study_course(current_user, db)
    return CourseRead.model_validate(course)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course_by_id(
    course_id: uuid.UUID,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Return a single course by ID."""
    course = await get_course(course_id, db)
    return CourseRead.model_validate(course)


@router.get("/{course_id}/students", response_model=Page[CourseStudentRead])
async def list_course_students(
    course_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Page[CourseStudentRead]:
    """Return paginated student enrollments for a course."""
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_course_students(current_user, course_id, params, db)
    return Page.create(
        items=[CourseStudentRead.model_validate(student) for student in items],
        total=total,
        params=params,
    )


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


@router.post(
    "/{course_id}/documents/zip",
    response_model=ZipImportResultRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_documents_from_zip(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ZipImportResultRead:
    """Extract a zip archive and stage all supported files as pending-add source materials."""
    staged, skipped_names = await stage_course_documents_from_zip(current_user, course_id, file, db)
    return ZipImportResultRead(
        staged=[CourseDocumentRead.model_validate(doc) for doc in staged],
        staged_count=len(staged),
        skipped_count=len(skipped_names),
        skipped_names=skipped_names,
    )


@router.delete("/{course_id}/documents", status_code=status.HTTP_200_OK)
async def remove_all_documents(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Stage all documents in a course for removal.

    Pending-add documents are deleted immediately. Active documents are
    transitioned to pending_remove and will be purged on the next rebuild.
    Returns the count of affected documents.
    """
    affected = await stage_all_course_documents_removal(current_user, course_id, db)
    return {"removed": affected}


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


@router.get("/{course_id}/instructions", response_model=CourseInstructionsRead)
async def read_course_instructions(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourseInstructionsRead:
    """Return the current course-specific prompt instructions for a course."""
    return await get_course_specific_instructions(current_user, course_id, db)


@router.post(
    "/{course_id}/enrollment-imports/preview",
    response_model=EnrollmentImportPreviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def preview_enrollment_csv(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentImportPreviewRead:
    """Parse a CSV of student emails and stage a preview for confirmation."""
    return await preview_enrollment_import(current_user, course_id, file, db)


@router.post(
    "/{course_id}/enrollment-imports/{preview_id}/confirm",
    response_model=EnrollmentImportConfirmRead,
)
async def confirm_enrollment_csv(
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentImportConfirmRead:
    """Confirm a staged enrollment import and delete the preview entry."""
    return await confirm_enrollment_import(current_user, course_id, preview_id, db)


@router.delete(
    "/{course_id}/enrollment-imports/{preview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_enrollment_csv(
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a staged enrollment import and delete the preview entry."""
    await cancel_enrollment_import(current_user, course_id, preview_id, db)


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


@router.delete("/{course_id}/enrollments", status_code=status.HTTP_200_OK)
async def remove_all_student_enrollments(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove all student enrollments from a course. Teacher or admin only."""
    removed = await unenroll_all_students(current_user, course_id, db)
    return {"removed": removed}


@router.delete("/{course_id}/enrollments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enrollment(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a user from a course."""
    await unenroll_user(current_user, course_id, user_id, db)
