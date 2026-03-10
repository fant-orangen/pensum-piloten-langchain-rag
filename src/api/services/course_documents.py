"""Course document management and versioned rebuild orchestration."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import uuid
from datetime import datetime
from functools import partial
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_session_factory
from src.api.models.course import Course
from src.api.models.course_document import CourseDocument
from src.api.models.user import User
from src.api.schemas.course import CourseMaterialsStatusRead
from src.api.utils import (
    bind_log_context,
    get_service_logger,
    require_course_teacher_or_admin,
    log_course_material_rebuild,
    log_course_material_rebuild_failed,
    log_course_material_rebuild_missing_course,
    log_course_material_rebuild_step,
)
from src.config import get_settings
from src.config.settings import PROJECT_ROOT
from src.ingestion.chunker import chunk_documents
from src.ingestion.loader import is_supported_document_path, load_documents_from_paths
from src.kg.extractor import extract_triplets, make_chunk_id
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


def build_course_documents_dir(course_code: str) -> Path:
    settings = get_settings()
    return Path(settings.documents_dir) / course_code


def build_course_scope_name(course_code: str, index_version: int) -> str:
    return f"{course_code}_v{index_version}"


def _resolve_documents_root(course: Course) -> Path:
    raw = Path(course.documents_dir)
    if raw.is_absolute():
        return raw
    return PROJECT_ROOT / raw


def get_course_artifacts_dir(course: Course) -> Path:
    return _resolve_documents_root(course) / COURSE_ARTIFACTS_DIRNAME


def _is_course_artifact_path(course: Course, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(_resolve_documents_root(course).resolve())
    except ValueError:
        return False
    return bool(relative.parts) and relative.parts[0] == COURSE_ARTIFACTS_DIRNAME


def _sanitize_filename(filename: str | None) -> str:
    candidate = Path(filename or "document").name.strip() or "document"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", candidate)


def _build_scope_name(course: Course, index_version: int) -> str:
    return build_course_scope_name(course.code, index_version)


async def _get_course_for_teacher(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalars().first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

    await require_course_teacher_or_admin(current_user, course_id, db)
    return course


def _ensure_not_rebuilding(course: Course) -> None:
    if course.rebuild_status in {COURSE_REBUILD_QUEUED, COURSE_REBUILD_BUILDING}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course materials are currently being rebuilt.",
        )


async def _pending_counts(course_id: uuid.UUID, db: AsyncSession) -> tuple[int, int]:
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
    now = datetime.utcnow()
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
        "rebuilt_at": datetime.utcnow().isoformat(),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def stage_course_documents(
    current_user: User,
    course_id: uuid.UUID,
    files: list[UploadFile],
    db: AsyncSession,
) -> list[CourseDocument]:
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")

    storage_root = _resolve_documents_root(course)
    storage_root.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []
    created_docs: list[CourseDocument] = []
    now = datetime.utcnow()

    try:
        for upload in files:
            safe_name = _sanitize_filename(upload.filename)
            if not is_supported_document_path(Path(safe_name)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type for '{safe_name}'.",
                )

            doc_id = uuid.uuid4()
            stored_name = f"{doc_id.hex}_{safe_name}"
            target_path = storage_root / stored_name
            target_path.write_bytes(await upload.read())
            written_paths.append(target_path)

            document = CourseDocument(
                id=doc_id,
                course_id=course.id,
                original_filename=safe_name,
                storage_path=str(target_path),
                content_type=upload.content_type,
                status=DOC_STATUS_PENDING_ADD,
                created_at=now,
                updated_at=now,
            )
            db.add(document)
            created_docs.append(document)

        await db.commit()
        for document in created_docs:
            await db.refresh(document)
        return created_docs
    except Exception:
        await db.rollback()
        for written_path in written_paths:
            if written_path.exists():
                written_path.unlink(missing_ok=True)
        raise


async def stage_course_document_removal(
    current_user: User,
    course_id: uuid.UUID,
    document_id: uuid.UUID,
    db: AsyncSession,
) -> None:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if document.status == DOC_STATUS_PENDING_ADD:
        path = Path(document.storage_path)
        if path.exists():
            path.unlink(missing_ok=True)
        await db.delete(document)
        await db.commit()
        return

    if document.status == DOC_STATUS_ACTIVE:
        document.status = DOC_STATUS_PENDING_REMOVE
        document.updated_at = datetime.utcnow()
        db.add(document)
        await db.commit()
        return

    await db.commit()


async def get_course_materials_status(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> CourseMaterialsStatusRead:
    course = await _get_course_for_teacher(current_user, course_id, db)
    return await build_course_materials_status(course, db)


async def queue_course_material_rebuild(
    current_user: User,
    course_id: uuid.UUID,
    db: AsyncSession,
) -> CourseMaterialsStatusRead:
    course = await _get_course_for_teacher(current_user, course_id, db)
    _ensure_not_rebuilding(course)

    pending_additions, pending_removals = await _pending_counts(course_id, db)
    if pending_additions == 0 and pending_removals == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No staged course material changes to apply.",
        )

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
    result = await db.execute(
        select(CourseDocument).where(CourseDocument.course_id == course_id)
    )
    documents = list(result.scalars().all())
    removed_paths: list[Path] = []
    now = datetime.utcnow()

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


async def run_course_material_rebuild(course_id: uuid.UUID) -> None:
    """Build a new course-scoped vector/KG partition and swap it in atomically."""
    session_factory = get_session_factory()
    rebuild_logger = bind_log_context(logger, course_id=course_id)
    target_scope: str | None = None
    old_scope: str | None = None
    removed_paths: list[Path] = []

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

        for removed_path in removed_paths:
            if removed_path.exists():
                removed_path.unlink(missing_ok=True)

        if old_scope and old_scope != target_scope:
            log_course_material_rebuild_step(
                rebuild_logger,
                step="cleanup_old_scope",
                old_scope=old_scope,
                target_scope=target_scope,
            )
            await asyncio.to_thread(delete_vectorstore, old_scope)
            kg_store = KGStore()
            try:
                await asyncio.to_thread(kg_store.clear, old_scope)
            finally:
                kg_store.close()
        elif old_scope and target_scope is None:
            log_course_material_rebuild_step(
                rebuild_logger,
                step="cleanup_old_scope",
                old_scope=old_scope,
                target_scope=None,
            )
            await asyncio.to_thread(delete_vectorstore, old_scope)
            kg_store = KGStore()
            try:
                await asyncio.to_thread(kg_store.clear, old_scope)
            finally:
                kg_store.close()

        log_course_material_rebuild(
            rebuild_logger,
            "complete",
            old_scope=old_scope,
            scope=target_scope,
            removed_file_count=len(removed_paths),
        )
    except Exception as exc:
        log_course_material_rebuild_failed(rebuild_logger, error=exc)
        if target_scope is not None:
            await asyncio.to_thread(delete_vectorstore, target_scope)
            kg_store = KGStore()
            try:
                await asyncio.to_thread(kg_store.clear, target_scope)
            finally:
                kg_store.close()
        await _set_rebuild_failure(course_id, str(exc))


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
