"""Course document management and versioned rebuild orchestration."""

from __future__ import annotations

import asyncio
import io
import json
import re
import shutil
import uuid
import zipfile
from functools import partial
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_session_factory
from src.api.models.course import Course
from src.api.models.course_document import CourseDocument
from src.api.models.time import utc_now
from src.api.models.user import User
from src.api.schemas.course import CourseMaterialsStatusRead
from src.api.utils.exception_util import bad_request_error, conflict_error, not_found_error
from src.api.utils import (
    bind_log_context,
    get_service_logger,
    require_course_teacher_or_admin,
    log_course_material_rebuild,
    log_course_material_rebuild_failed,
    log_course_material_rebuild_missing_course,
    log_course_material_rebuild_step,
)
from src.api.utils.logging_util import ServiceLogger
from src.config import get_settings
from src.config.settings import PROJECT_ROOT
from src.ingestion.chunk_ids import make_chunk_id
from src.ingestion.chunker import chunk_documents
from src.ingestion.loader import is_supported_document_path, load_documents_from_paths
from src.kg.extractor import extract_triplets
from src.kg.store import KGStore
from src.vectorstore import build_vectorstore, delete_vectorstore

logger = get_service_logger(__name__)

COURSE_REBUILD_IDLE = "idle"
COURSE_REBUILD_QUEUED = "queued"
COURSE_REBUILD_BUILDING = "building"
COURSE_REBUILD_FAILED = "failed"

DOC_STATUS_ACTIVE = "active"
DOC_STATUS_PENDING_ADD = "pending_add"
DOC_STATUS_PENDING_REMOVE = "pending_remove"
COURSE_ARTIFACTS_DIRNAME = ".pensum_piloten"
_MAX_ZIP_NESTING_DEPTH = 3
_UPLOAD_READ_CHUNK_BYTES = 1024 * 1024


def build_course_documents_dir(course_code: str) -> Path:
    """Return the filesystem path where documents for a course are stored."""
    settings = get_settings()
    return Path(settings.documents_dir) / course_code


def build_course_scope_name(course_code: str, index_version: int) -> str:
    """Return the ChromaDB/KG collection name for a given course and index version."""
    return f"{course_code}_v{index_version}"


def _resolve_documents_root(course: Course) -> Path:
    """Resolve the course documents directory to an absolute path."""
    raw = Path(course.documents_dir)
    if raw.is_absolute():
        return raw
    return PROJECT_ROOT / raw


def get_course_artifacts_dir(course: Course) -> Path:
    """Return the hidden artifacts directory inside the course documents root."""
    return _resolve_documents_root(course) / COURSE_ARTIFACTS_DIRNAME


def _is_course_artifact_path(course: Course, path: Path) -> bool:
    """Return True if the given path lives inside the course artifacts directory."""
    try:
        relative = path.resolve().relative_to(_resolve_documents_root(course).resolve())
    except ValueError:
        return False
    return bool(relative.parts) and relative.parts[0] == COURSE_ARTIFACTS_DIRNAME


def _sanitize_filename(filename: str | None) -> str:
    """Strip path components and replace unsafe characters with underscores."""
    candidate = Path(filename or "document").name.strip() or "document"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", candidate)


def _build_scope_name(course: Course, index_version: int) -> str:
    """Return the versioned collection scope name for the given course."""
    return build_course_scope_name(course.code, index_version)


def _payload_too_large_error(detail: str) -> HTTPException:
    """Return an HTTP 413 error for uploads that exceed configured limits."""
    return HTTPException(status_code=413, detail=detail)


def _format_bytes(num_bytes: int) -> str:
    """Format a byte count for concise user-facing validation errors."""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes // (1024 * 1024)} MB"
    if num_bytes >= 1024:
        return f"{num_bytes // 1024} KB"
    return f"{num_bytes} bytes"


async def _read_upload_limited(upload: UploadFile, *, max_bytes: int, label: str) -> bytes:
    """Read an UploadFile in bounded chunks, raising before buffering too much data."""
    chunks: list[bytes] = []
    total_bytes = 0
    while True:
        chunk = await upload.read(_UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise _payload_too_large_error(
                f"{label} exceeds the maximum size of {_format_bytes(max_bytes)}."
            )
        chunks.append(chunk)
    return b"".join(chunks)


async def _get_course_for_teacher(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> Course:
    """Fetch a course and verify the caller has teacher or admin access.

    Raises 404 if the course does not exist, 403 if access is denied.
    """
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if course is None:
        raise not_found_error("Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)
    return course


def _ensure_not_rebuilding(course: Course) -> None:
    """Raise HTTP 409 if a rebuild is already queued or running for the course."""
    if course.rebuild_status in {COURSE_REBUILD_QUEUED, COURSE_REBUILD_BUILDING}:
        raise conflict_error("Course materials are currently being rebuilt.")


async def _pending_counts(course_id: uuid.UUID, db: AsyncSession) -> tuple[int, int]:
    """Return (pending_additions, pending_removals) counts for a course."""
    pending_add_result = await db.execute(
        select(func.count())
        .select_from(CourseDocument)
        .where(
            CourseDocument.course_id == course_id,
            CourseDocument.status == DOC_STATUS_PENDING_ADD,
        )
    )
    pending_remove_result = await db.execute(
        select(func.count())
        .select_from(CourseDocument)
        .where(
            CourseDocument.course_id == course_id,
            CourseDocument.status == DOC_STATUS_PENDING_REMOVE,
        )
    )
    return int(pending_add_result.scalar_one()), int(pending_remove_result.scalar_one())


async def build_course_materials_status(
    course: Course,
    db: AsyncSession,
) -> CourseMaterialsStatusRead:
    """Assemble the current materials status (rebuild state, version, pending counts) for a course."""
    pending_additions, pending_removals = await _pending_counts(course.id, db)
    return CourseMaterialsStatusRead(
        course_id=course.id,
        rebuild_status=course.rebuild_status,
        rebuild_error=course.rebuild_error,
        index_version=course.index_version,
        active_scope=course.chroma_collection,
        pending_additions=pending_additions,
        pending_removals=pending_removals,
    )


async def list_course_documents(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> list[CourseDocument]:
    """Return all document records for a course, ordered by upload time. Requires teacher or admin."""
    await _get_course_for_teacher(current_user, course_id, db)
    result = await db.execute(
        select(CourseDocument)
        .where(CourseDocument.course_id == course_id)
        .order_by(CourseDocument.created_at.asc())
    )
    return list(result.scalars().all())


async def sync_course_documents_from_directory(
    course: Course,
    db: AsyncSession,
) -> int:
    """Ensure active CourseDocument rows exist for files currently on disk."""
    storage_root = _resolve_documents_root(course)
    if not storage_root.exists() or not storage_root.is_dir():
        return 0

    result = await db.execute(
        select(CourseDocument).where(CourseDocument.course_id == course.id)
    )
    existing_paths = {document.storage_path for document in result.scalars().all()}

    created_count = 0
    now = utc_now()
    for path in sorted(storage_root.rglob("*")):
        resolved_path = path.resolve()
        if not resolved_path.is_file():
            continue
        if _is_course_artifact_path(course, resolved_path):
            continue
        if not is_supported_document_path(resolved_path):
            continue

        storage_path = str(resolved_path)
        if storage_path in existing_paths:
            continue

        db.add(
            CourseDocument(
                course_id=course.id,
                original_filename=resolved_path.name,
                storage_path=storage_path,
                status=DOC_STATUS_ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
        existing_paths.add(storage_path)
        created_count += 1

    return created_count


def _clear_course_artifacts(course: Course) -> None:
    """Delete the course artifacts directory and all its contents."""
    artifacts_dir = get_course_artifacts_dir(course)
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir, ignore_errors=True)


def _write_course_artifacts(
    course: Course,
    *,
    scope: str,
    index_version: int,
    snapshot_documents: list[CourseDocument],
    triplets: list,
    chunk_count: int,
) -> None:
    """Persist KG triplets and a rebuild manifest to the course artifacts directory."""
    artifacts_dir = get_course_artifacts_dir(course)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    triplets_path = artifacts_dir / "kg_triplets.json"
    triplets_payload = [
        {
            "head": triplet.head,
            "relation": triplet.relation,
            "tail": triplet.tail,
            "chunk_id": triplet.chunk_id,
        }
        for triplet in triplets
    ]
    triplets_path.write_text(
        json.dumps(triplets_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest_path = artifacts_dir / "rebuild_manifest.json"
    manifest = {
        "course_id": str(course.id),
        "course_code": course.code,
        "scope": scope,
        "index_version": index_version,
        "documents_dir": str(_resolve_documents_root(course)),
        "document_count": len(snapshot_documents),
        "chunk_count": chunk_count,
        "triplet_count": len(triplets),
        "documents": [
            {
                "document_id": str(document.id),
                "original_filename": document.original_filename,
                "storage_path": document.storage_path,
            }
            for document in snapshot_documents
        ],
        "rebuilt_at": utc_now().isoformat(),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _extract_zip_files(
    zip_bytes: bytes,
    max_files: int,
    *,
    _collected: list[tuple[str, bytes]],
    _skipped: list[str],
    max_file_bytes: int,
    max_total_uncompressed_bytes: int,
    max_archive_bytes: int,
    max_compression_ratio: float,
    _total_uncompressed: list[int],
    _depth: int = 0,
) -> None:
    """Recursively extract supported files from a zip archive.

    Populates *_collected* with (display_name, file_bytes) pairs and *_skipped*
    with names of unsupported or over-limit files. Nested zips are expanded up
    to _MAX_ZIP_NESTING_DEPTH levels deep.
    """
    if _depth > _MAX_ZIP_NESTING_DEPTH:
        _skipped.append("<zip nested too deeply, skipped>")
        return
    if len(zip_bytes) > max_archive_bytes:
        raise _payload_too_large_error(
            f"Zip archive exceeds the maximum size of {_format_bytes(max_archive_bytes)}."
        )
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            entries = [info for info in zf.infolist() if not info.is_dir()]
            declared_uncompressed = sum(info.file_size for info in entries)
            if declared_uncompressed > max_total_uncompressed_bytes:
                raise _payload_too_large_error(
                    "Zip archive expands beyond the maximum total size of "
                    f"{_format_bytes(max_total_uncompressed_bytes)}."
                )
            compression_ratio = declared_uncompressed / max(len(zip_bytes), 1)
            if zip_bytes and compression_ratio > max_compression_ratio:
                raise bad_request_error("Zip archive compression ratio is too high.")

            for info in entries:
                member_path = Path(info.filename)
                # Skip macOS metadata entries (.__MACOSX dir, ._* resource forks, .DS_Store)
                if (
                    "__MACOSX" in member_path.parts
                    or member_path.name.startswith("._")
                    or member_path.name == ".DS_Store"
                ):
                    continue
                if _total_uncompressed[0] + info.file_size > max_total_uncompressed_bytes:
                    raise _payload_too_large_error(
                        "Zip archive expands beyond the maximum total size of "
                        f"{_format_bytes(max_total_uncompressed_bytes)}."
                    )
                if member_path.suffix.lower() == ".zip":
                    if info.file_size > max_archive_bytes:
                        raise _payload_too_large_error(
                            "Nested zip archive exceeds the maximum size of "
                            f"{_format_bytes(max_archive_bytes)}."
                        )
                    _total_uncompressed[0] += info.file_size
                    _extract_zip_files(
                        zf.read(info),
                        max_files,
                        _collected=_collected,
                        _skipped=_skipped,
                        max_file_bytes=max_file_bytes,
                        max_total_uncompressed_bytes=max_total_uncompressed_bytes,
                        max_archive_bytes=max_archive_bytes,
                        max_compression_ratio=max_compression_ratio,
                        _total_uncompressed=_total_uncompressed,
                        _depth=_depth + 1,
                    )
                elif info.file_size == 0:
                    _skipped.append(info.filename)
                elif is_supported_document_path(member_path):
                    if len(_collected) >= max_files:
                        _skipped.append(info.filename)
                    elif info.file_size > max_file_bytes:
                        _skipped.append(info.filename)
                    else:
                        _total_uncompressed[0] += info.file_size
                        _collected.append((info.filename, zf.read(info)))
                else:
                    _skipped.append(info.filename)
    except (zipfile.BadZipFile, RuntimeError):
        # BadZipFile: corrupted archive. RuntimeError: password-protected archive.
        _skipped.append("<invalid or encrypted zip file>")


async def _stage_raw_files(
    course: Course,
    storage_root: Path,
    file_payloads: list[tuple[str, bytes, str | None]],
    db: AsyncSession,
) -> list[CourseDocument]:
    """Write files to disk and register them as pending-add documents.

    Each payload is (display_name, data, content_type). *display_name* is stored
    as original_filename; the on-disk name is derived from its sanitised basename.
    Does not commit — callers must commit or rollback. Cleans up any written files
    if an exception occurs mid-loop.
    """
    written_paths: list[Path] = []
    created_docs: list[CourseDocument] = []
    now = utc_now()
    try:
        for display_name, data, content_type in file_payloads:
            safe_name = _sanitize_filename(display_name)
            doc_id = uuid.uuid4()
            stored_name = f"{doc_id.hex}_{safe_name}"
            target_path = storage_root / stored_name
            target_path.write_bytes(data)
            written_paths.append(target_path)
            document = CourseDocument(
                id=doc_id,
                course_id=course.id,
                original_filename=display_name,
                storage_path=str(target_path),
                content_type=content_type,
                status=DOC_STATUS_PENDING_ADD,
                created_at=now,
                updated_at=now,
            )
            db.add(document)
            created_docs.append(document)
        return created_docs
    except Exception:
        for written_path in written_paths:
            written_path.unlink(missing_ok=True)
        raise


async def stage_course_documents(
    current_user: User,
    course_id: uuid.UUID,
    files: list[UploadFile],
    db: AsyncSession,
) -> list[CourseDocument]:
    """Save uploaded files to disk and register them as pending-add documents.

    File names are sanitised and prefixed with a UUID to avoid collisions.
    Raises 400 for unsupported file types or an empty upload list, 409 if a rebuild is in progress.
    """
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    if not files:
        raise bad_request_error("No files uploaded.")

    settings = get_settings()
    if len(files) > settings.document_max_upload_files:
        raise _payload_too_large_error(
            f"Upload contains more than {settings.document_max_upload_files} files."
        )

    payloads: list[tuple[str, bytes, str | None]] = []
    total_payload_bytes = 0
    for upload in files:
        safe_name = _sanitize_filename(upload.filename)
        if not is_supported_document_path(Path(safe_name)):
            raise bad_request_error(f"Unsupported file type for '{safe_name}'.")
        data = await _read_upload_limited(
            upload,
            max_bytes=settings.document_max_file_bytes,
            label=f"Uploaded file '{safe_name}'",
        )
        total_payload_bytes += len(data)
        if total_payload_bytes > settings.document_max_total_upload_bytes:
            raise _payload_too_large_error(
                "Uploaded files exceed the maximum total size of "
                f"{_format_bytes(settings.document_max_total_upload_bytes)}."
            )
        payloads.append(
            (
                safe_name,
                data,
                upload.content_type,
            )
        )

    storage_root = _resolve_documents_root(course)
    storage_root.mkdir(parents=True, exist_ok=True)

    try:
        created_docs = await _stage_raw_files(course, storage_root, payloads, db)
        await db.commit()
        for document in created_docs:
            await db.refresh(document)
        return created_docs
    except Exception:
        await db.rollback()
        raise


async def stage_course_documents_from_zip(
    current_user: User,
    course_id: uuid.UUID,
    zip_file: UploadFile,
    db: AsyncSession,
) -> tuple[list[CourseDocument], list[str]]:
    """Extract a zip archive and stage all supported files as pending-add documents.

    Returns (staged_documents, skipped_names). Unsupported files and files beyond
    the zip_max_files limit are silently skipped. Nested zips are expanded
    recursively up to _MAX_ZIP_NESTING_DEPTH levels.
    Raises 400 if the archive contains no supported files, 409 if rebuilding.
    """
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    settings = get_settings()
    zip_bytes = await _read_upload_limited(
        zip_file,
        max_bytes=settings.zip_max_archive_bytes,
        label="Zip archive",
    )

    collected: list[tuple[str, bytes]] = []
    skipped: list[str] = []
    _extract_zip_files(
        zip_bytes,
        settings.zip_max_files,
        _collected=collected,
        _skipped=skipped,
        max_file_bytes=settings.document_max_file_bytes,
        max_total_uncompressed_bytes=settings.zip_max_uncompressed_bytes,
        max_archive_bytes=settings.zip_max_archive_bytes,
        max_compression_ratio=settings.zip_max_compression_ratio,
        _total_uncompressed=[0],
    )

    if not collected:
        raise bad_request_error("The zip archive contains no supported document files.")

    payloads: list[tuple[str, bytes, str | None]] = [
        (display_name, data, None) for display_name, data in collected
    ]

    storage_root = _resolve_documents_root(course)
    storage_root.mkdir(parents=True, exist_ok=True)

    try:
        created_docs = await _stage_raw_files(course, storage_root, payloads, db)
        await db.commit()
        for document in created_docs:
            await db.refresh(document)
        return created_docs, skipped
    except Exception:
        await db.rollback()
        raise


async def stage_course_document_removal(
    current_user: User,
    course_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Stage a document for removal or delete it outright if it was never activated.

    Documents in pending_add state are deleted immediately (file and row).
    Documents in active state are transitioned to pending_remove; the file is
    removed only when the next rebuild completes successfully.
    Raises 404 if the document is not found, 409 if a rebuild is in progress.
    """
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    result = await db.execute(
        select(CourseDocument).where(
            CourseDocument.id == document_id,
            CourseDocument.course_id == course_id,
        )
    )
    document = result.scalars().first()
    if document is None:
        raise not_found_error("Document not found.")

    if document.status == DOC_STATUS_PENDING_ADD:
        path = Path(document.storage_path)
        if path.exists():
            path.unlink(missing_ok=True)
        await db.delete(document)
        await db.commit()
        return

    if document.status == DOC_STATUS_ACTIVE:
        document.status = DOC_STATUS_PENDING_REMOVE
        document.updated_at = utc_now()
        db.add(document)
        await db.commit()
        return

    await db.commit()


async def get_course_materials_status(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> CourseMaterialsStatusRead:
    """Return the materials rebuild status for a course. Requires teacher or admin."""
    course = await _get_course_for_teacher(current_user, course_id, db)
    return await build_course_materials_status(course, db)


async def queue_course_material_rebuild(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> CourseMaterialsStatusRead:
    """Transition a course to queued rebuild state so the background task can pick it up.

    Raises 400 if there are no staged changes to apply, 409 if a rebuild is already in progress.
    Returns the updated materials status.
    """
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    pending_additions, pending_removals = await _pending_counts(course_id, db)
    if pending_additions == 0 and pending_removals == 0:
        raise bad_request_error("No staged course material changes to apply.")

    course.rebuild_status = COURSE_REBUILD_QUEUED
    course.rebuild_error = None
    db.add(course)
    await db.commit()
    await db.refresh(course)
    log_course_material_rebuild(
        bind_log_context(logger, course_id=course.id),
        "queued",
        pending_additions=pending_additions,
        pending_removals=pending_removals,
        current_scope=course.chroma_collection,
        next_index_version=course.index_version + 1,
    )
    return await build_course_materials_status(course, db)


async def _get_snapshot_documents(course_id: uuid.UUID, db: AsyncSession) -> list[CourseDocument]:
    """Return the set of documents that should be included in the next build.

    Active documents and pending-add documents are included; pending-remove documents are excluded.
    """
    result = await db.execute(
        select(CourseDocument)
        .where(
            CourseDocument.course_id == course_id,
            CourseDocument.status.in_([DOC_STATUS_ACTIVE, DOC_STATUS_PENDING_ADD]),
        )
        .order_by(CourseDocument.created_at.asc())
    )
    documents = list(result.scalars().all())
    return [doc for doc in documents if doc.status != DOC_STATUS_PENDING_REMOVE]


async def _activate_staged_documents(course_id: uuid.UUID, db: AsyncSession) -> list[Path]:
    """Promote pending-add documents to active and delete pending-remove rows.

    Returns the file paths of removed documents so they can be unlinted after the DB commit.
    """
    result = await db.execute(
        select(CourseDocument).where(CourseDocument.course_id == course_id)
    )
    documents = list(result.scalars().all())
    removed_paths: list[Path] = []
    now = utc_now()

    for document in documents:
        if document.status == DOC_STATUS_PENDING_ADD:
            document.status = DOC_STATUS_ACTIVE
            document.updated_at = now
            db.add(document)
        elif document.status == DOC_STATUS_PENDING_REMOVE:
            removed_paths.append(Path(document.storage_path))
            await db.delete(document)

    return removed_paths


async def _set_rebuild_failure(
    course_id: uuid.UUID,
    error_message: str,
) -> None:
    """Persist a FAILED rebuild status and truncated error message on the course row."""
    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(Course).where(Course.id == course_id))
        course = result.scalars().first()
        if course is None:
            return
        course.rebuild_status = COURSE_REBUILD_FAILED
        course.rebuild_error = error_message[:1000]
        db.add(course)
        await db.commit()


def _delete_course_scope(scope: str) -> None:
    """Delete both persisted retrieval stores for a course material scope."""
    delete_vectorstore(scope)
    kg_store = KGStore()
    try:
        kg_store.clear(scope)
    finally:
        kg_store.close()


async def _cleanup_failed_target_scope(
    target_scope: str | None,
    rebuild_logger: ServiceLogger,
) -> None:
    """Best-effort cleanup for a candidate scope that failed before activation."""
    if target_scope is None:
        return
    try:
        await asyncio.to_thread(_delete_course_scope, target_scope)
    except Exception as cleanup_exc:
        rebuild_logger.warning(
            "course_material_rebuild_failed_target_cleanup_failed",
            target_scope=target_scope,
            error=str(cleanup_exc),
        )


async def _cleanup_after_activation(
    *,
    removed_paths: list[Path],
    old_scope: str | None,
    target_scope: str | None,
    rebuild_logger: ServiceLogger,
) -> None:
    """Clean old files and retrieval stores after the new scope is active.

    This cleanup runs only after the database has committed the new active
    scope, so failures here must not trigger deletion of ``target_scope``.
    """
    cleanup_errors: list[str] = []
    for removed_path in removed_paths:
        if removed_path.exists():
            try:
                removed_path.unlink(missing_ok=True)
            except Exception as exc:
                cleanup_errors.append(f"failed to remove {removed_path}: {exc}")

    if old_scope and old_scope != target_scope:
        log_course_material_rebuild_step(
            rebuild_logger,
            step="cleanup_old_scope",
            old_scope=old_scope,
            target_scope=target_scope,
        )
        try:
            await asyncio.to_thread(_delete_course_scope, old_scope)
        except Exception as exc:
            cleanup_errors.append(f"failed to cleanup old scope {old_scope}: {exc}")

    if cleanup_errors:
        raise RuntimeError("; ".join(cleanup_errors))


async def run_course_material_rebuild(course_id: uuid.UUID) -> None:
    """Build a new course-scoped vector/KG partition and swap it in atomically."""
    session_factory = get_session_factory()
    rebuild_logger = bind_log_context(logger, course_id=course_id)
    target_scope: str | None = None
    old_scope: str | None = None
    removed_paths: list[Path] = []
    activated = False

    try:
        async with session_factory() as db:
            result = await db.execute(select(Course).where(Course.id == course_id))
            course = result.scalars().first()
            if course is None:
                log_course_material_rebuild_missing_course(rebuild_logger)
                return

            course.rebuild_status = COURSE_REBUILD_BUILDING
            course.rebuild_error = None
            db.add(course)
            await db.commit()
            await db.refresh(course)

            rebuild_logger = bind_log_context(logger, course_id=course.id)
            snapshot_documents = await _get_snapshot_documents(course.id, db)
            next_version = course.index_version + 1
            old_scope = course.chroma_collection
            log_course_material_rebuild(
                rebuild_logger,
                "started",
                old_scope=old_scope,
                next_index_version=next_version,
                snapshot_document_count=len(snapshot_documents),
            )

            if snapshot_documents:
                target_scope = _build_scope_name(course, next_version)
                paths = [Path(doc.storage_path) for doc in snapshot_documents]
                log_course_material_rebuild_step(
                    rebuild_logger,
                    step="load_documents",
                    target_scope=target_scope,
                    file_count=len(paths),
                )
                documents = await asyncio.to_thread(load_documents_from_paths, paths)
                if not documents:
                    raise ValueError("No supported course documents were available for ingestion.")

                log_course_material_rebuild_step(
                    rebuild_logger,
                    step="chunk_documents",
                    target_scope=target_scope,
                    document_count=len(documents),
                )
                chunks = await asyncio.to_thread(chunk_documents, documents)
                log_course_material_rebuild_step(
                    rebuild_logger,
                    step="assign_chunk_ids",
                    target_scope=target_scope,
                    chunk_count=len(chunks),
                )
                for chunk in chunks:
                    chunk.metadata["chunk_id"] = make_chunk_id(chunk)

                log_course_material_rebuild_step(
                    rebuild_logger,
                    step="build_vectorstore",
                    target_scope=target_scope,
                    chunk_count=len(chunks),
                )
                await asyncio.to_thread(
                    partial(
                        build_vectorstore,
                        chunks,
                        collection_name=target_scope,
                        replace=True,
                    )
                )
                triplets = []
                if course.rag_mode == "kg_rag":
                    log_course_material_rebuild_step(
                        rebuild_logger,
                        step="extract_triplets",
                        target_scope=target_scope,
                        chunk_count=len(chunks),
                    )
                    triplets = await asyncio.to_thread(extract_triplets, chunks)
                    log_course_material_rebuild_step(
                        rebuild_logger,
                        step="build_knowledge_graph",
                        target_scope=target_scope,
                        triplet_count=len(triplets),
                    )
                    kg_store = KGStore()
                    try:
                        await asyncio.to_thread(kg_store.build_kg, triplets, target_scope)
                    finally:
                        kg_store.close()
                else:
                    log_course_material_rebuild_step(
                        rebuild_logger,
                        step="skip_knowledge_graph",
                        target_scope=target_scope,
                        rag_mode=course.rag_mode,
                    )
                log_course_material_rebuild_step(
                    rebuild_logger,
                    step="write_course_artifacts",
                    target_scope=target_scope,
                    artifacts_dir=get_course_artifacts_dir(course),
                )
                await asyncio.to_thread(
                    _write_course_artifacts,
                    course,
                    scope=target_scope,
                    index_version=next_version,
                    snapshot_documents=snapshot_documents,
                    triplets=triplets,
                    chunk_count=len(chunks),
                )
            else:
                log_course_material_rebuild_step(
                    rebuild_logger,
                    step="clear_active_scope",
                    old_scope=old_scope,
                )
                await asyncio.to_thread(_clear_course_artifacts, course)

            removed_paths = await _activate_staged_documents(course.id, db)
            log_course_material_rebuild_step(
                rebuild_logger,
                step="activate_staged_documents",
                removed_file_count=len(removed_paths),
                target_scope=target_scope,
            )

            course.index_version = next_version
            course.chroma_collection = target_scope if snapshot_documents else None
            course.rebuild_status = COURSE_REBUILD_IDLE
            course.rebuild_error = None
            db.add(course)
            await db.commit()
            activated = True

        try:
            await _cleanup_after_activation(
                removed_paths=removed_paths,
                old_scope=old_scope,
                target_scope=target_scope,
                rebuild_logger=rebuild_logger,
            )
        except Exception as cleanup_exc:
            rebuild_logger.warning(
                "course_material_rebuild_cleanup_failed",
                old_scope=old_scope,
                target_scope=target_scope,
                error=str(cleanup_exc),
            )

        log_course_material_rebuild(
            rebuild_logger,
            "complete",
            old_scope=old_scope,
            scope=target_scope,
            removed_file_count=len(removed_paths),
        )
    except Exception as exc:
        log_course_material_rebuild_failed(rebuild_logger, error=exc)
        if not activated:
            await _cleanup_failed_target_scope(target_scope, rebuild_logger)
        await _set_rebuild_failure(course_id, str(exc))


async def stage_all_course_documents_removal(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> int:
    """Stage all documents in a course for removal.

    Documents in *pending_add* state are deleted immediately (file and DB row).
    Documents in *active* state are transitioned to *pending_remove*; the files
    are removed only when the next rebuild completes.
    Documents already in *pending_remove* state are left unchanged.

    Returns the total number of documents affected.
    Raises 409 if a rebuild is currently queued or running.
    """
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    result = await db.execute(
        select(CourseDocument).where(CourseDocument.course_id == course_id)
    )
    documents = list(result.scalars().all())

    affected = 0
    now = utc_now()
    for document in documents:
        if document.status == DOC_STATUS_PENDING_ADD:
            path = Path(document.storage_path)
            path.unlink(missing_ok=True)
            await db.delete(document)
            affected += 1
        elif document.status == DOC_STATUS_ACTIVE:
            document.status = DOC_STATUS_PENDING_REMOVE
            document.updated_at = now
            db.add(document)
            affected += 1

    await db.commit()
    return affected


async def purge_course_materials(course: Course, db: AsyncSession) -> None:
    """Delete all document rows/files and active course-scoped vector/KG data."""
    result = await db.execute(select(CourseDocument).where(CourseDocument.course_id == course.id))
    documents = list(result.scalars().all())
    file_paths = [Path(document.storage_path) for document in documents]

    for document in documents:
        await db.delete(document)

    if course.chroma_collection:
        await asyncio.to_thread(delete_vectorstore, course.chroma_collection)
        kg_store = KGStore()
        try:
            await asyncio.to_thread(kg_store.clear, course.chroma_collection)
        finally:
            kg_store.close()

    for file_path in file_paths:
        if file_path.exists():
            file_path.unlink(missing_ok=True)

    storage_root = _resolve_documents_root(course)
    if storage_root.exists():
        shutil.rmtree(storage_root, ignore_errors=True)
