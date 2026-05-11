"""Test data seeding for Pensum Piloten.

This module provides an asynchronous `seed()` function to insert a canonical set of test users, courses, and enrollments into the database.
It is used during development/testing to ensure the application can start with known test data for local exercise, UI flows, and early feature validation.

## Activation

Seeding is activated by setting `SEED_TEST_DATA=true` in the environment or a `.env` file.
When enabled, the `seed()` function should be called once on startup (typically in the FastAPI startup handler).

## What gets seeded?

- **Users**: One teacher, one student, one admin (ids and emails are consistent across runs).
- **Courses**: A main test course (_COURSE_CODE = "TEST101", instructor: teacher), and a second test course ("TEST102", instructor: admin).
- **Enrollments**:
    - The student is enrolled in the main test course as a student.
    - The teacher is enrolled as a teacher in TEST101 and (for UI flows) as a *student* in TEST102.
- **Directories**: Document directories are created if missing. Course documents may be synced from their directory.
- **RAG/KG index**: Course metadata (chroma_collection, index_version) is loaded from a local manifest if present (see `.pensum_piloten/rebuild_manifest.json`).

Idempotency is enforced: if the objects exist, nothing is duplicated or changed except for (instructive) metadata updates and roles.

## Usage pattern

This function is safe to call multiple times or on every startup. It will provision the known users, courses, and document state needed to exercise the API and frontend UI.

"""

import json
import re

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation  # noqa: F401 — keep metadata complete
from src.api.models.course import Course
from src.api.models.enrollment import CourseEnrollment
from src.api.models.user import User
from src.api.services.auth import hash_password
from src.api.services.course_documents import (
    build_course_documents_dir,
    build_course_scope_name,
    sync_course_documents_from_directory,
)
from src.vectorstore.store import _get_client as _get_chroma_client

logger = structlog.get_logger(__name__)

# -----------------------------
# Constants for canonical test data
# -----------------------------
_TEACHER_EMAIL = "teacher@test.com"
_TEACHER2_EMAIL = "teacher2@test.com"
_STUDENT_EMAIL = "student@test.com"
_ADMIN_EMAIL = "admin@test.com"
_COURSE_CODE = "TEST101"
_SECOND_COURSE_CODE = "TEST102"
_COURSE_SPECIFIC_INSTRUCTIONS = (
    "This course is specifically about understanding NTFS when discussing file systems. "
    "When file-system concepts are explained, always describe them with reference to NTFS."
)
_COURSE_ARTIFACTS_DIRNAME = ".pensum_piloten"
_REBUILD_MANIFEST_NAME = "rebuild_manifest.json"


def _find_latest_chroma_collection(course_code: str) -> tuple[str, int] | None:
    """Find the highest-versioned Chroma collection for *course_code*.

    Returns (collection_name, version) or None if no matching collection exists.
    """
    try:
        client = _get_chroma_client()
        pattern = re.compile(rf"^{re.escape(course_code)}_v(\d+)$")
        best: tuple[str, int] | None = None
        for col in client.list_collections():
            m = pattern.match(col.name)
            if m:
                version = int(m.group(1))
                if best is None or version > best[1]:
                    best = (col.name, version)
        return best
    except Exception:
        logger.warning("seed_chroma_lookup_failed", course=course_code)
        return None


def _load_seed_scope_from_manifest(course_code: str) -> tuple[str, int]:
    """Return (chroma_collection, index_version) for the given course code, using a manifest if present.

    This function is used to align the course's document indexing state (version/scope)
    with the actual ChromaDB/materialized index on disk. If the manifest file does not exist,
    a fallback default scope and index_version (1) is used.

    Args:
        course_code: The course code (e.g., 'TEST101').

    Returns:
        Tuple of (chroma_collection: str, index_version: int).
    """
    course_dir = build_course_documents_dir(course_code)
    manifest_path = course_dir / _COURSE_ARTIFACTS_DIRNAME / _REBUILD_MANIFEST_NAME
    fallback_scope = build_course_scope_name(course_code, 1)
    fallback_version = 1

    if not manifest_path.exists():
        return fallback_scope, fallback_version

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        logger.warning("seed_manifest_unreadable", course=course_code, path=str(manifest_path))
        return fallback_scope, fallback_version

    scope = payload.get("scope")
    index_version = payload.get("index_version")
    if not isinstance(scope, str) or not scope.strip():
        return fallback_scope, fallback_version
    if not isinstance(index_version, int) or index_version < 1:
        return scope.strip(), fallback_version
    return scope.strip(), index_version


async def seed(db: AsyncSession) -> None:
    """
    Populate canonical test users, courses, and their relationships in the database for dev/test/demo.

    - Creates admin, teacher, student (with fixed credentials).
    - Creates two test courses. Main course uses chroma_collection/index_version from local manifest if present.
    - Ensures enrollments for test flows (incl. teacher enrolled as student in course 2).
    - Invokes sync from doc directory for seeded course.
    - Idempotent: skips/updates, does not duplicate.
    """
    test_course_dir = build_course_documents_dir(_COURSE_CODE)
    second_course_dir = build_course_documents_dir(_SECOND_COURSE_CODE)
    test_course_scope, test_course_version = _load_seed_scope_from_manifest(_COURSE_CODE)
    second_course_scope, second_course_version = _load_seed_scope_from_manifest(_SECOND_COURSE_CODE)
    test_course_dir.mkdir(parents=True, exist_ok=True)
    second_course_dir.mkdir(parents=True, exist_ok=True)

    # --- Admin ---
    admin = await _get_or_create_user(
        db,
        email=_ADMIN_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Admin",
        global_role="admin",
    )

    # --- Teacher ---
    teacher = await _get_or_create_user(
        db,
        email=_TEACHER_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Teacher",
        global_role="teacher",
    )

    # --- Teacher 2 ---
    teacher2 = await _get_or_create_user(
        db,
        email=_TEACHER2_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Teacher2",
        global_role="teacher",
    )

    # --- Student ---
    student = await _get_or_create_user(
        db,
        email=_STUDENT_EMAIL,
        password="password123",
        first_name="Test",
        last_name="Student",
        global_role="student",
    )

    # --- Additional test students ---
    test_students = []
    for i in range(1, 6):
        ts = await _get_or_create_user(
            db,
            email=f"test{i}@test.com",
            password="password123",
            first_name=f"Test{i}",
            last_name="Student",
            global_role="student",
        )
        test_students.append(ts)

    # --- Course ---
    course_result = await db.execute(select(Course).where(Course.code == _COURSE_CODE))
    course = course_result.scalars().first()
    if course is None:
        course = Course(
            name="Test Course",
            code=_COURSE_CODE,
            chroma_collection=test_course_scope,
            documents_dir=str(test_course_dir),
            rag_mode="kg_rag",
            course_specific_instructions=_COURSE_SPECIFIC_INSTRUCTIONS,
            index_version=test_course_version,
            created_by_id=teacher.id,
        )
        db.add(course)
        await db.flush()  # populate course.id before using it below
        logger.info("seed_created_course", code=_COURSE_CODE)
    else:
        course.documents_dir = str(test_course_dir)
        course.course_specific_instructions = _COURSE_SPECIFIC_INSTRUCTIONS
        # Reconcile chroma_collection with what actually exists in Chroma
        latest = _find_latest_chroma_collection(_COURSE_CODE)
        if latest and latest[0] != course.chroma_collection:
            logger.info(
                "seed_reconcile_chroma",
                code=_COURSE_CODE,
                old=course.chroma_collection,
                new=latest[0],
            )
            course.chroma_collection = latest[0]
            course.index_version = max(course.index_version, latest[1])
        db.add(course)
        logger.info("seed_course_exists", code=_COURSE_CODE)

    # --- Second Course ---
    second_course_result = await db.execute(select(Course).where(Course.code == _SECOND_COURSE_CODE))
    second_course = second_course_result.scalars().first()
    if second_course is None:
        second_course = Course(
            name="Second Test Course",
            code=_SECOND_COURSE_CODE,
            chroma_collection=second_course_scope,
            documents_dir=str(second_course_dir),
            rag_mode="kg_rag",
            index_version=second_course_version,
            created_by_id=admin.id,
        )
        db.add(second_course)
        await db.flush()
        logger.info("seed_created_course", code=_SECOND_COURSE_CODE)
    else:
        second_course.documents_dir = str(second_course_dir)
        # Reconcile chroma_collection with what actually exists in Chroma
        latest = _find_latest_chroma_collection(_SECOND_COURSE_CODE)
        if latest and latest[0] != second_course.chroma_collection:
            logger.info(
                "seed_reconcile_chroma",
                code=_SECOND_COURSE_CODE,
                old=second_course.chroma_collection,
                new=latest[0],
            )
            second_course.chroma_collection = latest[0]
            second_course.index_version = max(second_course.index_version, latest[1])
        db.add(second_course)
        logger.info("seed_course_exists", code=_SECOND_COURSE_CODE)

    # --- Enrollment ---
    # Student enrolled in TEST101 as student
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == student.id,
            CourseEnrollment.course_id == course.id,
        )
    )
    if enrollment_result.scalars().first() is None:
        db.add(CourseEnrollment(user_id=student.id, course_id=course.id, role="student"))
        logger.info("seed_enrolled_student", email=_STUDENT_EMAIL, course=_COURSE_CODE)

    # Teacher enrolled in TEST101 as teacher
    teacher_enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == teacher.id,
            CourseEnrollment.course_id == course.id,
        )
    )
    if teacher_enrollment_result.scalars().first() is None:
        db.add(CourseEnrollment(user_id=teacher.id, course_id=course.id, role="teacher"))
        logger.info("seed_enrolled_teacher", email=_TEACHER_EMAIL, course=_COURSE_CODE)

    # Teacher2 enrolled in TEST101 as teacher
    teacher2_enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == teacher2.id,
            CourseEnrollment.course_id == course.id,
        )
    )
    if teacher2_enrollment_result.scalars().first() is None:
        db.add(CourseEnrollment(user_id=teacher2.id, course_id=course.id, role="teacher"))
        logger.info("seed_enrolled_teacher2", email=_TEACHER2_EMAIL, course=_COURSE_CODE)

    # Teacher2 enrolled in TEST102 as teacher
    teacher2_second_enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == teacher2.id,
            CourseEnrollment.course_id == second_course.id,
        )
    )
    if teacher2_second_enrollment_result.scalars().first() is None:
        db.add(CourseEnrollment(user_id=teacher2.id, course_id=second_course.id, role="teacher"))
        logger.info("seed_enrolled_teacher2", email=_TEACHER2_EMAIL, course=_SECOND_COURSE_CODE)

    # Additional test students enrolled in TEST101
    for ts in test_students:
        ts_enrollment_result = await db.execute(
            select(CourseEnrollment).where(
                CourseEnrollment.user_id == ts.id,
                CourseEnrollment.course_id == course.id,
            )
        )
        if ts_enrollment_result.scalars().first() is None:
            db.add(CourseEnrollment(user_id=ts.id, course_id=course.id, role="student"))
            logger.info("seed_enrolled_test_student", email=ts.email, course=_COURSE_CODE)

    # Teacher enrolled in TEST102 as student (for UI/role switching flows)
    second_course_teacher_enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == teacher.id,
            CourseEnrollment.course_id == second_course.id,
        )
    )
    second_course_teacher_enrollment = second_course_teacher_enrollment_result.scalars().first()
    if second_course_teacher_enrollment is None:
        db.add(CourseEnrollment(user_id=teacher.id, course_id=second_course.id, role="student"))
        logger.info("seed_enrolled_teacher", email=_TEACHER_EMAIL, course=_SECOND_COURSE_CODE, role="student")
    elif second_course_teacher_enrollment.role != "student":
        # Non-idempotent: forcibly update teacher's enrollment to 'student'
        second_course_teacher_enrollment.role = "student"
        db.add(second_course_teacher_enrollment)
        logger.info(
            "seed_updated_teacher_enrollment",
            email=_TEACHER_EMAIL,
            course=_SECOND_COURSE_CODE,
            role="student",
        )

    await _seed_course_documents(db, course)
    await db.commit()
    logger.info("seed_complete")


async def _get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    global_role: str,
) -> User:
    """
    Idempotently create a User with fixed credentials, or return existing (logs event).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            global_role=global_role,
        )
        db.add(user)
        await db.flush()  # populate user.id before referencing it
        logger.info("seed_created_user", email=email, role=global_role)
    else:
        logger.info("seed_user_exists", email=email)
    return user


async def _seed_course_documents(db: AsyncSession, course: Course) -> None:
    """
    Synchronize course documents from course's directory for the given Course.

    Only logs if new documents are discovered.
    """
    created_count = await sync_course_documents_from_directory(course, db)
    if created_count:
        logger.info("seed_course_documents_created", course=course.code, count=created_count)
