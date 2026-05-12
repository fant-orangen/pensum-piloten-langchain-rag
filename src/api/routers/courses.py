"""Course endpoints — course CRUD, enrollment management, and document ingestion.

Includes sub-resources for source documents (upload, stage, rebuild),
enrollment imports (CSV preview/confirm), and course-specific prompt instructions.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_app_user
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
    CourseSummaryRead,
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
    cancel_enrollment_import,
    confirm_enrollment_import,
    create_course,
    delete_course,
    enroll_user,
    get_all_teachers,
    get_course_summary_for_user,
    get_course_specific_instructions,
    get_available_courses,
    get_course_students,
    get_course_teachers,
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
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses the authenticated user is enrolled in.

    Args:
        current_user: User resolved from the bearer token.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
    """
    courses = await get_enrolled_courses(current_user.id, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/available", response_model=list[CourseRead])
async def list_available_courses(
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses where the authenticated user is enrolled as a student.

    Args:
        current_user: User resolved from the bearer token.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
    """
    courses = await get_available_courses(current_user.id, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/responsible", response_model=list[CourseRead])
async def list_responsible_courses(
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseRead]:
    """Return all courses where the authenticated user is enrolled as a teacher.

    Args:
        current_user: User resolved from the bearer token; must be teacher/admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller is not a teacher or admin.
    """
    courses = await get_responsible_courses(current_user, db)
    return [CourseRead.model_validate(c) for c in courses]


@router.get("/all-teachers", response_model=list[CourseStudentRead])
async def list_all_teachers(
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseStudentRead]:
    """Return all users with global teacher role.

    Args:
        current_user: User resolved from the bearer token; must be teacher/admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller is not a teacher or admin.
    """
    teachers = await get_all_teachers(current_user, db)
    return [CourseStudentRead.model_validate(t) for t in teachers]


@router.get("/{course_id}", response_model=CourseSummaryRead)
async def get_course_by_id(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> CourseSummaryRead:
    """Return safe course metadata for chat/sidebar display.

    Args:
        course_id: Course to read.
        current_user: User resolved from the bearer token.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller is not enrolled in the course and is not admin.
        404: Course does not exist.
        422: Invalid course_id path value.
    """
    course = await get_course_summary_for_user(current_user, course_id, db)
    return CourseSummaryRead.model_validate(course)


@router.get("/{course_id}/students", response_model=Page[CourseStudentRead])
async def list_course_students(
    course_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> Page[CourseStudentRead]:
    """Return paginated student enrollments for a course.

    Args:
        course_id: Course whose students should be listed.
        page: One-based page number.
        page_size: Number of students per page, capped at 100.
        search: Optional case-insensitive filter for name or email.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid UUID or pagination query value.
    """
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_course_students(current_user, course_id, params, db, search)
    return Page.create(
        items=[CourseStudentRead.model_validate(student) for student in items],
        total=total,
        params=params,
    )


@router.get("/{course_id}/teachers", response_model=Page[CourseStudentRead])
async def list_course_teachers(
    course_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> Page[CourseStudentRead]:
    """Return paginated teacher enrollments for a course.

    Args:
        course_id: Course whose teachers should be listed.
        page: One-based page number.
        page_size: Number of teachers per page, capped at 100.
        current_user: User resolved from the bearer token; must own the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller is not course owner/admin.
        404: Course does not exist.
        422: Invalid UUID or pagination query value.
    """
    params = PaginationParams(page=page, page_size=page_size)
    items, total = await get_course_teachers(current_user, course_id, params, db)
    return Page.create(
        items=[CourseStudentRead.model_validate(teacher) for teacher in items],
        total=total,
        params=params,
    )


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def new_course(
    body: CourseCreate,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Create a new course.

    Args:
        body: Course creation payload.
        current_user: User resolved from the bearer token; must be teacher/admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller is not teacher/admin.
        409: Course code already exists.
        422: Invalid request body.
    """
    course = await create_course(current_user, body, db)
    return CourseRead.model_validate(course)


@router.get("/{course_id}/documents", response_model=list[CourseDocumentRead])
async def list_documents(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseDocumentRead]:
    """List staged and active source materials for a course.

    Args:
        course_id: Course whose document records should be listed.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid course_id path value.
    """
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
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourseDocumentRead]:
    """Stage new source materials for a course.

    Args:
        course_id: Course receiving the uploaded files.
        files: Multipart files to store as pending additions.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        400: File type is unsupported or no valid files were supplied.
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        409: Course materials are already queued/building.
        413: Upload exceeds configured size limits.
        422: Invalid multipart request or UUID.
    """
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
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> ZipImportResultRead:
    """Extract a zip archive and stage supported files as pending-add materials.

    Args:
        course_id: Course receiving the extracted files.
        file: Multipart zip archive.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        400: Upload is not a valid zip or contains no supported files.
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        409: Course materials are already queued/building.
        413: Upload exceeds configured size limits.
        422: Invalid multipart request or UUID.
    """
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
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Stage all documents in a course for removal.

    Pending-add documents are deleted immediately. Active documents are
    transitioned to pending_remove and will be purged on the next rebuild.
    Returns the count of affected documents.

    Args:
        course_id: Course whose documents should be staged for removal.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        409: Course materials are already queued/building.
        422: Invalid course_id path value.
    """
    affected = await stage_all_course_documents_removal(current_user, course_id, db)
    return {"removed": affected}


@router.delete("/{course_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(
    course_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Stage removal of a source document from a course.

    Active documents move to pending_remove; pending-add documents are deleted
    immediately. Requires course teacher or admin.

    Args:
        course_id: Course containing the document.
        document_id: Document record to remove or stage for removal.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course or document does not exist.
        409: Course materials are already queued/building.
        422: Invalid UUID path value.
    """
    await stage_course_document_removal(current_user, course_id, document_id, db)


@router.get("/{course_id}/documents/status", response_model=CourseMaterialsStatusRead)
async def get_documents_status(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialsStatusRead:
    """Return current rebuild state and pending document counts for a course.

    Args:
        course_id: Course whose material status should be read.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid course_id path value.
    """
    return await get_course_materials_status(current_user, course_id, db)


@router.post(
    "/{course_id}/documents/confirm",
    response_model=CourseMaterialsStatusRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def confirm_document_changes(
    course_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> CourseMaterialsStatusRead:
    """Confirm all staged add/remove changes and start a versioned rebuild.

    Returns 202 with the queued status. Raises 409 if another rebuild is
    already queued/running or there are no staged changes.

    Args:
        course_id: Course whose staged document changes should be activated.
        background_tasks: FastAPI background task manager used to run rebuild work.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        409: Rebuild is already queued/running or no staged changes exist.
        422: Invalid course_id path value.
    """
    course_status = await queue_course_material_rebuild(current_user, course_id, db)
    background_tasks.add_task(run_course_material_rebuild, course_id)
    return course_status


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a course and its conversations, enrollments, and material indexes.

    Requires course owner or admin. Raises 409 while materials are rebuilding.

    Args:
        course_id: Course to delete.
        current_user: User resolved from the bearer token; must own the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller is not course owner/admin.
        404: Course does not exist.
        409: Course materials are queued/building.
        422: Invalid course_id path value.
    """
    await delete_course(current_user, course_id, db)


@router.patch("/{course_id}/instructions", response_model=CourseRead)
async def update_course_instructions(
    course_id: uuid.UUID,
    body: CourseInstructionsUpdate,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> CourseRead:
    """Update the course-specific prompt instructions for a course.

    Args:
        course_id: Course whose instructions should be updated.
        body: New instruction text; blank text clears existing instructions.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid UUID or request body.
    """
    course = await update_course_specific_instructions(current_user, course_id, body, db)
    return CourseRead.model_validate(course)


@router.get("/{course_id}/instructions", response_model=CourseInstructionsRead)
async def read_course_instructions(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> CourseInstructionsRead:
    """Return the current course-specific prompt instructions for a course.

    Args:
        course_id: Course whose instructions should be read.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid course_id path value.
    """
    return await get_course_specific_instructions(current_user, course_id, db)


@router.post(
    "/{course_id}/enrollment-imports/preview",
    response_model=EnrollmentImportPreviewRead,
    status_code=status.HTTP_201_CREATED,
)
async def preview_enrollment_csv(
    course_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentImportPreviewRead:
    """Parse a CSV of student emails and stage a preview for confirmation.

    Does not mutate enrollments. Raises 400 for invalid/empty CSV input.

    Args:
        course_id: Course receiving the imported student enrollments.
        file: UTF-8 CSV upload with email and optional first/last name columns.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        400: CSV is invalid, non-UTF-8, or contains no valid email rows.
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid multipart request or UUID.
    """
    return await preview_enrollment_import(current_user, course_id, file, db)


@router.post(
    "/{course_id}/enrollment-imports/{preview_id}/confirm",
    response_model=EnrollmentImportConfirmRead,
)
async def confirm_enrollment_csv(
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentImportConfirmRead:
    """Confirm a staged enrollment import and delete the preview entry.

    Creates placeholder user accounts for missing candidates and enrolls all
    eligible addresses from the preview.

    Args:
        course_id: Course receiving the imported enrollments.
        preview_id: Previously created import preview to apply.
        current_user: User resolved from the bearer token; must own the preview or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller cannot access the course or did not create the preview.
        404: Course or preview does not exist.
        422: Invalid UUID path value.
    """
    return await confirm_enrollment_import(current_user, course_id, preview_id, db)


@router.delete(
    "/{course_id}/enrollment-imports/{preview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_enrollment_csv(
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel a staged enrollment import and delete the preview entry.

    Args:
        course_id: Course associated with the preview.
        preview_id: Preview to discard.
        current_user: User resolved from the bearer token; must own the preview or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller cannot access the course or did not create the preview.
        404: Course or preview does not exist.
        422: Invalid UUID path value.
    """
    await cancel_enrollment_import(current_user, course_id, preview_id, db)


@router.post(
    "/{course_id}/enrollments",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_enrollment(
    course_id: uuid.UUID,
    body: EnrollmentCreate,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> EnrollmentRead:
    """Enroll a user in a course by email.

    Requires teacher/admin access to the course. Raises 404 for unknown users
    and 409 when the enrollment already exists.

    Args:
        course_id: Course receiving the enrollment.
        body: Target user email and role to assign.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        400: Enrollment role is unsupported.
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course or target user does not exist.
        409: User is already enrolled.
        422: Invalid UUID or request body.
    """
    enrollment = await enroll_user(current_user, course_id, body, db)
    return EnrollmentRead.model_validate(enrollment)


@router.delete("/{course_id}/enrollments", status_code=status.HTTP_200_OK)
async def remove_all_student_enrollments(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove all student enrollments from a course.

    Args:
        course_id: Course whose student enrollments should be removed.
        current_user: User resolved from the bearer token; must teach the course or be admin.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks course teacher/admin access.
        404: Course does not exist.
        422: Invalid course_id path value.
    """
    removed = await unenroll_all_students(current_user, course_id, db)
    return {"removed": removed}


@router.delete("/{course_id}/enrollments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_enrollment(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a user from a course.

    Teachers can remove students. Course owners/admins can also remove course
    teachers, except the course owner.

    Args:
        course_id: Course containing the enrollment.
        user_id: User enrollment to remove.
        current_user: User resolved from the bearer token.
        db: Request-scoped database session.

    Raises:
        401: Missing, expired, or invalid bearer token.
        403: Caller lacks permission to remove this enrollment.
        404: Course or enrollment does not exist.
        409: Attempted to remove the course owner.
        422: Invalid UUID path value.
    """
    await unenroll_user(current_user, course_id, user_id, db)
