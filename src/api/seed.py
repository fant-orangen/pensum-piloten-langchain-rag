"""Seed the dedicated operating-systems experiment dataset."""

import json
import shutil
from pathlib import Path

import structlog
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.conversation import Conversation  # noqa: F401 — keep metadata complete
from src.api.models.course import Course
from src.api.models.course_document import CourseDocument
from src.api.models.enrollment import CourseEnrollment
from src.api.models.message import Message
from src.api.models.user import User
from src.api.services.auth import hash_password
from src.api.services.course_documents import (
    build_course_documents_dir,
    build_course_scope_name,
    purge_course_materials,
    sync_course_documents_from_directory,
)

logger = structlog.get_logger(__name__)

_TEACHER_EMAIL = "teacher@test.com"
_ADMIN_EMAIL = "admin@test.com"
_COURSE_ARTIFACTS_DIRNAME = ".pensum_piloten"
_REBUILD_MANIFEST_NAME = "rebuild_manifest.json"
_LEGACY_TEST_COURSE_CODES = ("TEST101", "TEST102")
_RAG_COURSE_CODE = "os_g1"
_SYS_COURSE_CODE = "os_g2"
_CONTROL_COURSE_CODE = "os_g3"
_EXPERIMENT_PASSWORD = "password123"
_OPERATING_SYSTEMS_NAME = "Operating Systems"

_EXPERIMENT_COURSES = (
    {
        "code": _RAG_COURSE_CODE,
        "rag_mode": "kg_rag",
        "use_manifest": True,
    },
    {
        "code": _SYS_COURSE_CODE,
        "rag_mode": "no_rag",
        "use_manifest": False,
    },
    {
        "code": _CONTROL_COURSE_CODE,
        "rag_mode": "no_rag",
        "use_manifest": False,
    },
)

_EXPERIMENT_USER_GROUPS = (
    (_RAG_COURSE_CODE, "g1u", 12),
    (_SYS_COURSE_CODE, "g2u", 12),
    (_CONTROL_COURSE_CODE, "g3u", 12),
)


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
    """Populate the test branch with course-coded experiment cohorts."""
    admin = await _get_or_create_user(
        db,
        email=_ADMIN_EMAIL,
        password=_EXPERIMENT_PASSWORD,
        first_name="Test",
        last_name="Admin",
        global_role="admin",
    )

    teacher = await _get_or_create_user(
        db,
        email=_TEACHER_EMAIL,
        password=_EXPERIMENT_PASSWORD,
        first_name="Test",
        last_name="Teacher",
        global_role="teacher",
    )

    await _promote_legacy_rag_materials()
    await _remove_legacy_test_courses(db)

    seeded_courses: dict[str, Course] = {}
    for course_config in _EXPERIMENT_COURSES:
        course = await _get_or_create_experiment_course(
            db,
            code=course_config["code"],
            created_by_id=teacher.id,
            rag_mode=course_config["rag_mode"],
            use_manifest=course_config["use_manifest"],
        )
        seeded_courses[course.code] = course

    for course in seeded_courses.values():
        await _ensure_course_enrollment(db, teacher.id, course.id, role="teacher")
    await _ensure_course_enrollment(db, admin.id, seeded_courses[_RAG_COURSE_CODE].id, role="teacher")

    all_study_course_ids = {c.id for c in seeded_courses.values()}

    for course_code, prefix, count in _EXPERIMENT_USER_GROUPS:
        course = seeded_courses[course_code]
        for index in range(1, count + 1):
            student = await _get_or_create_user(
                db,
                email=f"{prefix}{index}@test.com",
                password=_EXPERIMENT_PASSWORD,
                first_name="Test",
                last_name=f"{course_code.upper()} {index:02d}",
                global_role="student",
            )
            await _ensure_single_study_enrollment(db, student.id, course.id, all_study_course_ids)

    await _seed_course_documents(db, seeded_courses[_RAG_COURSE_CODE])
    await db.commit()
    logger.info("seed_complete")


async def _promote_legacy_rag_materials() -> None:
    """Copy legacy TEST101 materials into os_g1 when os_g1 is still empty."""
    legacy_dir = build_course_documents_dir(_LEGACY_TEST_COURSE_CODES[0])
    rag_dir = build_course_documents_dir(_RAG_COURSE_CODE)
    if not legacy_dir.exists():
        rag_dir.mkdir(parents=True, exist_ok=True)
        return

    rag_dir.mkdir(parents=True, exist_ok=True)
    if any(rag_dir.iterdir()):
        return

    shutil.copytree(legacy_dir, rag_dir, dirs_exist_ok=True)
    logger.info("seed_copied_legacy_rag_materials", source=str(legacy_dir), target=str(rag_dir))


async def _remove_legacy_test_courses(db: AsyncSession) -> None:
    """Delete the old TEST101/TEST102 seeded courses and their dependent rows."""
    result = await db.execute(
        select(Course).where(Course.code.in_(_LEGACY_TEST_COURSE_CODES))
    )
    legacy_courses = list(result.scalars().all())
    for course in legacy_courses:
        conversation_ids = (
            select(Conversation.id)
            .where(Conversation.course_id == course.id)
            .scalar_subquery()
        )
        await db.execute(sa_delete(Message).where(Message.conversation_id.in_(conversation_ids)))
        await db.execute(sa_delete(Conversation).where(Conversation.course_id == course.id))
        await db.execute(sa_delete(CourseDocument).where(CourseDocument.course_id == course.id))
        await db.execute(sa_delete(CourseEnrollment).where(CourseEnrollment.course_id == course.id))
        await purge_course_materials(course, db)
        await db.delete(course)
        logger.info("seed_removed_legacy_course", code=course.code)


async def _get_or_create_experiment_course(
    db: AsyncSession,
    *,
    code: str,
    created_by_id: object,
    rag_mode: str,
    use_manifest: bool,
) -> Course:
    """Create or update one experiment course."""
    course_dir = build_course_documents_dir(code)
    course_dir.mkdir(parents=True, exist_ok=True)
    if use_manifest:
        chroma_collection, index_version = _load_seed_scope_from_manifest(code)
    else:
        chroma_collection, index_version = None, 0

    course_result = await db.execute(select(Course).where(Course.code == code))
    course = course_result.scalars().first()
    if course is None:
        course = Course(
            name=_OPERATING_SYSTEMS_NAME,
            code=code,
            chroma_collection=chroma_collection,
            documents_dir=str(course_dir),
            rag_mode=rag_mode,
            course_specific_instructions=None,
            index_version=index_version,
            created_by_id=created_by_id,
        )
        db.add(course)
        await db.flush()
        logger.info("seed_created_course", code=code)
        return course

    course.name = _OPERATING_SYSTEMS_NAME
    course.rag_mode = rag_mode
    course.documents_dir = str(course_dir)
    course.created_by_id = created_by_id
    course.course_specific_instructions = None
    if use_manifest:
        course.chroma_collection = chroma_collection
        course.index_version = max(course.index_version, index_version)
    else:
        course.chroma_collection = None
        course.index_version = 0
    db.add(course)
    logger.info("seed_course_exists", code=code)
    return course


async def _ensure_single_study_enrollment(
    db: AsyncSession,
    user_id: object,
    target_course_id: object,
    all_study_course_ids: set,
) -> None:
    """Ensure the user holds exactly one student enrollment among the study courses.

    - If they have no study enrollment, enroll them in target_course_id.
    - If they already have exactly one study enrollment (even a different one from
      a prior advance), leave it untouched to preserve experiment progress.
    - If they somehow hold multiple study enrollments (the bug this fixes), remove
      all of them and re-enroll in target_course_id to restore a clean state.
    """
    result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id.in_(all_study_course_ids),
            CourseEnrollment.role == "student",
        )
    )
    existing = list(result.scalars().all())

    if len(existing) == 1:
        return  # already in a valid single-enrollment state; don't undo any advancement

    if len(existing) > 1:
        # Multiple enrollments — delete all non-target ones. Never delete-then-reinsert
        # the same (user_id, course_id) pair: that triggers a unique constraint violation
        # during SQLAlchemy's autoflush.
        has_target = any(e.course_id == target_course_id for e in existing)
        for e in existing:
            if e.course_id != target_course_id:
                await db.delete(e)
        logger.warning(
            "seed_repaired_duplicate_study_enrollments",
            user_id=str(user_id),
            removed=len(existing) - (1 if has_target else 0),
            reset_to=str(target_course_id),
        )
        if has_target:
            return  # target enrollment already present; extras removed above

    db.add(CourseEnrollment(user_id=user_id, course_id=target_course_id, role="student"))


async def _ensure_course_enrollment(
    db: AsyncSession,
    user_id: object,
    course_id: object,
    *,
    role: str,
) -> None:
    """Idempotently ensure one enrollment row with the requested role."""
    result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.user_id == user_id,
            CourseEnrollment.course_id == course_id,
        )
    )
    enrollment = result.scalars().first()
    if enrollment is None:
        db.add(CourseEnrollment(user_id=user_id, course_id=course_id, role=role))
        return
    if enrollment.role != role:
        enrollment.role = role
        db.add(enrollment)


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
