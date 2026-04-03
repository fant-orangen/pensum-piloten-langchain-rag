"""Course business logic and database queries."""

import csv
import uuid
from dataclasses import dataclass, field


from fastapi import UploadFile
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.exc import IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.enrollment_import_preview import EnrollmentImportPreview
from src.api.models.message import Message
from src.api.models.user import User
from src.api.schemas.course import CourseCreate, CourseInstructionsUpdate, EnrollmentCreate
from src.api.services.course_documents import (
    COURSE_REBUILD_BUILDING,
    COURSE_REBUILD_QUEUED,
    build_course_documents_dir,
    purge_course_materials,
)

from src.api.schemas.course import (
    CourseCreate,
    CourseInstructionsRead,
    CourseInstructionsUpdate,
    EnrollmentCreate,
    EnrollmentImportConfirmRead,
    EnrollmentImportPreviewRead,
    MissingCandidateRead,
)

from src.api.schemas.pagination import PaginationParams
from src.api.utils.exception_util import (
    bad_request_error,
    conflict_error,
    forbidden_error,
    not_found_error,
)
from src.api.utils import (
    require_course_owner_or_admin,
    require_course_teacher_or_admin,
    require_teacher_or_admin,
    require_unenroll_permission,
)

_EMAIL_ADAPTER = TypeAdapter(EmailStr)
_CSV_HEADER_VALUES = {"email", "emails", "student_email", "student_emails", "e-mail", "epost"}


@dataclass(slots=True)
class ParsedEnrollmentImport:
    """Result of parsing an enrollment CSV, categorised by validity and uniqueness."""

    total_rows: int
    accepted_emails: list[str]
    duplicate_emails: list[str]
    invalid_emails: list[str]
    candidate_names: dict[str, tuple[str, str]] = field(default_factory=dict)


async def get_enrolled_courses(user_id: uuid.UUID, db: AsyncSession) -> list[Course]:
    """Return all courses the given user is enrolled in."""
    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(CourseEnrollment.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_available_courses(user_id: uuid.UUID, db: AsyncSession) -> list[Course]:
    """Return all courses the given user is enrolled in as a student."""
    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.role == "student",
        )
    )
    return list(result.scalars().all())


async def get_responsible_courses(current_user: User, db: AsyncSession) -> list[Course]:
    """Return all courses where the given user is enrolled as a teacher."""
    require_teacher_or_admin(current_user)

    result = await db.execute(
        select(Course)
        .join(CourseEnrollment, CourseEnrollment.course_id == Course.id)
        .where(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.role == "teacher",
        )
    )
    return list(result.scalars().all())


async def get_course_students(
    current_user: User,
    course_id: uuid.UUID,
    params: PaginationParams,
    db: AsyncSession,
) -> tuple[list[User], int]:
    """Return a page of users enrolled in the course as students."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise not_found_error("Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    base = (
        select(User)
        .join(CourseEnrollment, CourseEnrollment.user_id == User.id)
        .where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.role == "student",
        )
    )

    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total: int = count_result.scalar_one()

    result = await db.execute(
        base.order_by(User.last_name.asc(), User.first_name.asc(), User.email.asc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    items = list(result.scalars().all())

    return items, total


async def create_course(current_user: User, body: CourseCreate, db: AsyncSession) -> Course:
    """Create a new course and enroll the creating user as a teacher.

    Raises 403 if the user lacks the teacher or admin role.
    Raises 409 if the course code is already taken.
    """
    require_teacher_or_admin(current_user)

    existing = await db.execute(select(Course).where(Course.code == body.code))
    if existing.scalars().first() is not None:
        raise conflict_error(f"A course with code '{body.code}' already exists.")

    course_documents_dir = build_course_documents_dir(body.code)
    course_documents_dir.mkdir(parents=True, exist_ok=True)

    course = Course(
        name=body.name,
        code=body.code,
        chroma_collection=None,
        documents_dir=str(course_documents_dir),
        description=body.description,
        rag_mode=body.rag_mode,
        course_specific_instructions=body.course_specific_instructions,
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
        raise not_found_error("Course not found.")

    require_teacher_or_admin(current_user)
    require_course_owner_or_admin(current_user, course.created_by_id)
    if course.rebuild_status in {COURSE_REBUILD_QUEUED, COURSE_REBUILD_BUILDING}:
        raise conflict_error("Cannot delete a course while its materials are rebuilding.")

    conversation_ids = (
        select(Conversation.id)
        .where(Conversation.course_id == course_id)
        .scalar_subquery()
    )

    # Remove dependent rows in FK-safe order before deleting the course itself.
    await db.execute(sa_delete(Message).where(Message.conversation_id.in_(conversation_ids)))
    await db.execute(sa_delete(Conversation).where(Conversation.course_id == course_id))
    await purge_course_materials(course, db)
    await db.execute(sa_delete(CourseEnrollment).where(CourseEnrollment.course_id == course_id))
    await db.delete(course)
    await db.commit()


async def update_course_specific_instructions(
    current_user: User,
    course_id: uuid.UUID,
    body: CourseInstructionsUpdate,
    db: AsyncSession,
) -> Course:
    """Update teacher-authored prompt instructions for a course."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalars().first()
    if course is None:
        raise not_found_error("Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    cleaned_instructions = (
        body.course_specific_instructions.strip()
        if body.course_specific_instructions is not None
        else None
    )
    course.course_specific_instructions = cleaned_instructions or None
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def get_course_specific_instructions(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> CourseInstructionsRead:
    """Return the current teacher-authored instructions for a course."""
    course = await _get_course_or_404(course_id, db)
    await require_course_teacher_or_admin(current_user, course_id, db)
    return CourseInstructionsRead(
        course_id=course.id,
        course_specific_instructions=course.course_specific_instructions,
    )


def _normalise_email(email: str) -> str:
    """Strip whitespace and lower-case an email address for consistent comparison."""
    return email.strip().lower()


def _validate_email(email: str) -> str:
    """Normalise and validate an email address. Raises ValueError if invalid."""
    cleaned_email = _normalise_email(email)
    try:
        return str(_EMAIL_ADAPTER.validate_python(cleaned_email))
    except ValidationError as exc:
        raise ValueError("Invalid email address.") from exc


def _parse_enrollment_import_csv(content: str) -> ParsedEnrollmentImport:
    """Parse raw CSV text into accepted, duplicate, and invalid email buckets.

    Expects rows with 1–3 columns: email, optional first name, optional last name.
    An optional header row is detected when the first cell matches a known header value.
    Rows with fewer than 3 columns are accepted; missing name fields default to empty string.
    """
    accepted_emails: list[str] = []
    duplicate_emails: list[str] = []
    invalid_emails: list[str] = []
    candidate_names: dict[str, tuple[str, str]] = {}
    seen_emails: set[str] = set()
    seen_duplicates: set[str] = set()
    total_rows = 0
    saw_data_row = False

    for _row_number, row in enumerate(csv.reader(content.splitlines()), start=1):
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue

        # Detect optional header row (first non-empty row whose first cell is a known header).
        if not saw_data_row and cells[0].lower() in _CSV_HEADER_VALUES:
            saw_data_row = True
            continue

        saw_data_row = True
        total_rows += 1

        raw_email = cells[0] if cells else ""
        first_name = cells[1] if len(cells) > 1 else ""
        last_name = cells[2] if len(cells) > 2 else ""

        try:
            cleaned_email = _validate_email(raw_email)
        except ValueError:
            invalid_emails.append(raw_email)
            continue

        if cleaned_email in seen_emails:
            if cleaned_email not in seen_duplicates:
                duplicate_emails.append(cleaned_email)
                seen_duplicates.add(cleaned_email)
            continue

        seen_emails.add(cleaned_email)
        accepted_emails.append(cleaned_email)
        candidate_names[cleaned_email] = (first_name, last_name)

    return ParsedEnrollmentImport(
        total_rows=total_rows,
        accepted_emails=accepted_emails,
        duplicate_emails=duplicate_emails,
        invalid_emails=invalid_emails,
        candidate_names=candidate_names,
    )


async def _get_course_or_404(course_id: uuid.UUID, db: AsyncSession) -> Course:
    """Fetch a course by ID or raise HTTP 404."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if course is None:
        raise not_found_error("Course not found.")
    return course


async def _classify_import_candidates(
    course_id: uuid.UUID,
    candidate_emails: list[str],
    db: AsyncSession,
) -> tuple[list[str], list[str], list[str]]:
    """Split candidate emails into (enrollable, missing, already_enrolled) groups.

    - enrollable: emails matched to an existing user who is not yet enrolled.
    - missing: emails not found in the user table.
    - already_enrolled: emails matched to a user already enrolled in the course.
    """
    if not candidate_emails:
        return [], [], []

    user_result = await db.execute(
        select(User.id, User.email).where(func.lower(User.email).in_(candidate_emails))
    )
    matched_rows = list(user_result.all())
    user_ids_by_email = {
        _normalise_email(email): user_id for user_id, email in matched_rows
    }

    existing_emails = [email for email in candidate_emails if email in user_ids_by_email]
    missing_emails = [email for email in candidate_emails if email not in user_ids_by_email]
    if not existing_emails:
        return [], missing_emails, []

    enrolled_result = await db.execute(
        select(CourseEnrollment.user_id).where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.user_id.in_([user_ids_by_email[email] for email in existing_emails]),
        )
    )
    enrolled_user_ids = set(enrolled_result.scalars().all())

    enrollable_emails = [
        email for email in existing_emails if user_ids_by_email[email] not in enrolled_user_ids
    ]
    already_enrolled_emails = [
        email for email in existing_emails if user_ids_by_email[email] in enrolled_user_ids
    ]
    return enrollable_emails, missing_emails, already_enrolled_emails


async def _get_import_preview_for_actor(
    current_user: User,
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    db: AsyncSession,
) -> EnrollmentImportPreview:
    """Fetch an enrollment import preview, verifying course access and preview ownership.

    Raises 403 if the caller is not the teacher who created the preview (admins are exempt).
    Raises 404 if the preview does not exist for the given course.
    """
    await require_course_teacher_or_admin(current_user, course_id, db)

    preview_result = await db.execute(
        select(EnrollmentImportPreview).where(
            EnrollmentImportPreview.id == preview_id,
            EnrollmentImportPreview.course_id == course_id,
        )
    )
    preview = preview_result.scalars().first()
    if preview is None:
        raise not_found_error("Enrollment import preview not found.")

    if current_user.global_role != "admin" and preview.created_by_id != current_user.id:
        raise forbidden_error("Only the teacher who created this import preview can confirm or cancel it.")

    return preview


async def preview_enrollment_import(
    current_user: User,
    course_id: uuid.UUID,
    upload: UploadFile,
    db: AsyncSession,
) -> EnrollmentImportPreviewRead:
    """Parse a CSV of student emails and return an enrollment preview without committing any changes.

    Replaces any previous pending preview created by the same teacher for this course.
    Raises 400 if the file is not valid UTF-8 or contains no valid addresses.
    """
    await _get_course_or_404(course_id, db)
    await require_course_teacher_or_admin(current_user, course_id, db)

    try:
        content = (await upload.read()).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise bad_request_error("CSV file must be UTF-8 encoded.") from exc

    parsed = _parse_enrollment_import_csv(content)
    if not parsed.accepted_emails:
        raise bad_request_error("CSV did not contain any valid student email addresses.")

    enrollable_emails, missing_emails, already_enrolled_emails = await _classify_import_candidates(
        course_id,
        parsed.accepted_emails,
        db,
    )

    await db.execute(
        sa_delete(EnrollmentImportPreview).where(
            EnrollmentImportPreview.course_id == course_id,
            EnrollmentImportPreview.created_by_id == current_user.id,
        )
    )

    candidates_name_map = {
        email: {"first_name": names[0], "last_name": names[1]}
        for email, names in parsed.candidate_names.items()
    }

    preview = EnrollmentImportPreview(
        course_id=course_id,
        created_by_id=current_user.id,
        uploaded_filename=upload.filename,
        requested_role="student",
        candidate_emails=parsed.accepted_emails,
        candidates_name_map=candidates_name_map,
    )
    db.add(preview)
    await db.commit()
    await db.refresh(preview)

    missing_candidates = [
        MissingCandidateRead(
            email=email,
            first_name=(parsed.candidate_names.get(email, ("", ""))[0]),
            last_name=(parsed.candidate_names.get(email, ("", ""))[1]),
        )
        for email in missing_emails
    ]

    return EnrollmentImportPreviewRead(
        preview_id=preview.id,
        course_id=course_id,
        uploaded_filename=preview.uploaded_filename,
        requested_role=preview.requested_role,
        total_rows=parsed.total_rows,
        accepted_email_count=len(parsed.accepted_emails),
        enrollable_emails=enrollable_emails,
        missing_candidates=missing_candidates,
        already_enrolled_emails=already_enrolled_emails,
        duplicate_emails=parsed.duplicate_emails,
        invalid_emails=parsed.invalid_emails,
        has_warnings=bool(
            missing_emails
            or already_enrolled_emails
            or parsed.duplicate_emails
            or parsed.invalid_emails
        ),
    )


async def confirm_enrollment_import(
    current_user: User,
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    db: AsyncSession,
) -> EnrollmentImportConfirmRead:
    """Execute the enrollment import from a confirmed preview, then delete the preview row.

    Re-classifies candidates at confirm time to catch any changes since the preview was generated.
    Creates new student accounts for any emails without an existing user, using the name data
    stored in the preview. Raises 409 if a concurrent enrollment change causes an integrity conflict.
    """
    preview = await _get_import_preview_for_actor(current_user, course_id, preview_id, db)

    enrollable_emails, missing_emails, already_enrolled_emails = await _classify_import_candidates(
        course_id,
        list(preview.candidate_emails),
        db,
    )

    name_map: dict[str, dict[str, str]] = preview.candidates_name_map or {}
    created_emails: list[str] = []

    # Create accounts for students who don't have one yet, then enroll them.
    for email in missing_emails:
        names = name_map.get(email, {})
        new_user = User(
            email=email,
            hashed_password="",
            first_name=names.get("first_name", ""),
            last_name=names.get("last_name", ""),
            must_change_password=True,
        )
        db.add(new_user)
        created_emails.append(email)
        enrollable_emails.append(email)

    # Flush so newly created users get IDs before we build enrollments.
    await db.flush()

    if enrollable_emails:
        user_result = await db.execute(
            select(User.id, User.email).where(func.lower(User.email).in_(enrollable_emails))
        )
        user_ids_by_email = {
            _normalise_email(email): user_id for user_id, email in user_result.all()
        }
        for email in enrollable_emails:
            if email in user_ids_by_email:
                db.add(
                    CourseEnrollment(
                        user_id=user_ids_by_email[email],
                        course_id=course_id,
                        role=preview.requested_role,
                    )
                )

    await db.delete(preview)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise conflict_error("Enrollment import changed before confirmation. Preview again and retry.") from exc

    return EnrollmentImportConfirmRead(
        course_id=course_id,
        requested_role=preview.requested_role,
        enrolled_emails=enrollable_emails,
        created_emails=created_emails,
        already_enrolled_emails=already_enrolled_emails,
    )


async def cancel_enrollment_import(
    current_user: User,
    course_id: uuid.UUID,
    preview_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Delete a pending enrollment import preview without enrolling anyone."""
    preview = await _get_import_preview_for_actor(current_user, course_id, preview_id, db)
    await db.delete(preview)
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
    await _get_course_or_404(course_id, db)

    await require_course_teacher_or_admin(current_user, course_id, db)

    cleaned_user_email = _normalise_email(body.user_email)
    user_result = await db.execute(select(User).where(func.lower(User.email) == cleaned_user_email))
    target_user = user_result.scalars().first()
    if target_user is None:
        raise not_found_error(f"No user with email '{cleaned_user_email}' found.")

    dup_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == target_user.id,
            CourseEnrollment.course_id == course_id,
        )
    )
    if dup_result.scalars().first() is not None:
        raise conflict_error("User is already enrolled in this course.")

    enrollment = CourseEnrollment(
        user_id=target_user.id,
        course_id=course_id,
        role=body.role,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def unenroll_all_students(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    """Remove all student enrollments from a course.

    Raises 404 if the course does not exist.
    Raises 403 if the current user is not a teacher of the course or an admin.
    Returns the number of enrollments removed.
    """
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    if course_result.scalars().first() is None:
        raise not_found_error("Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)

    result = await db.execute(
        sa_delete(CourseEnrollment)
        .where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.role == "student",
        )
        .returning(CourseEnrollment.id)
    )
    removed = len(result.fetchall())
    await db.commit()
    return removed


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
        raise not_found_error("Course not found.")

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id,
        )
    )
    enrollment = enrollment_result.scalars().first()
    if enrollment is None:
        raise not_found_error("User is not enrolled in this course.")

    await require_unenroll_permission(current_user, enrollment, course, db)

    await db.delete(enrollment)
    await db.commit()
