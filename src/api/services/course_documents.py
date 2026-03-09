"""Course document management and versioned rebuild orchestration."""

from __future__ import annotations

import asyncio
import re
import shutil
import uuid
from datetime import datetime
from functools import partial
from pathlib import Path

import structlog
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.authorization import require_course_teacher_or_admin
from src.api.database import get_session_factory
from src.api.models.course import Course
from src.api.models.course_document import CourseDocument
from src.api.models.user import User
from src.api.schemas.course import CourseMaterialsStatusRead
from src.config.settings import PROJECT_ROOT
from src.ingestion.chunker import chunk_documents
from src.ingestion.loader import is_supported_document_path, load_documents_from_paths
from src.kg.extractor import extract_triplets, make_chunk_id
from src.kg.store import KGStore
from src.vectorstore import build_vectorstore, delete_vectorstore

logger = structlog.get_logger(__name__)

COURSE_REBUILD_IDLE = "idle"
COURSE_REBUILD_QUEUED = "queued"
COURSE_REBUILD_BUILDING = "building"
COURSE_REBUILD_FAILED = "failed"

DOC_STATUS_ACTIVE = "active"
DOC_STATUS_PENDING_ADD = "pending_add"
DOC_STATUS_PENDING_REMOVE = "pending_remove"


def _resolve_documents_root(course: Course) -> Path:
    raw = Path(course.documents_dir)
    if raw.is_absolute():
        return raw
    return PROJECT_ROOT / raw


def _sanitize_filename(filename: str | None) -> str:
    candidate = Path(filename or "document").name.strip() or "document"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", candidate)


def _build_scope_name(course_id: uuid.UUID, index_version: int) -> str:
    return f"course_{course_id.hex}_v{index_version}"


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
    target_scope: str | None = None
    old_scope: str | None = None
    removed_paths: list[Path] = []

    try:
        async with session_factory() as db:
            result = await db.execute(select(Course).where(Course.id == course_id))
            course = result.scalars().first()
            if course is None:
                return

            course.rebuild_status = COURSE_REBUILD_BUILDING
            course.rebuild_error = None
            db.add(course)
            await db.commit()
            await db.refresh(course)

            snapshot_documents = await _get_snapshot_documents(course.id, db)
            next_version = course.index_version + 1
            old_scope = course.chroma_collection

            if snapshot_documents:
                target_scope = _build_scope_name(course.id, next_version)
                paths = [Path(doc.storage_path) for doc in snapshot_documents]
                documents = await asyncio.to_thread(load_documents_from_paths, paths)
                if not documents:
                    raise ValueError("No supported course documents were available for ingestion.")

                chunks = await asyncio.to_thread(chunk_documents, documents)
                for chunk in chunks:
                    chunk.metadata["chunk_id"] = make_chunk_id(chunk)

                await asyncio.to_thread(
                    partial(
                        build_vectorstore,
                        chunks,
                        collection_name=target_scope,
                        replace=True,
                    )
                )
                triplets = await asyncio.to_thread(extract_triplets, chunks)
                kg_store = KGStore()
                try:
                    await asyncio.to_thread(kg_store.build_kg, triplets, target_scope)
                finally:
                    kg_store.close()

            removed_paths = await _activate_staged_documents(course.id, db)

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
            await asyncio.to_thread(delete_vectorstore, old_scope)
            kg_store = KGStore()
            try:
                await asyncio.to_thread(kg_store.clear, old_scope)
            finally:
                kg_store.close()
        elif old_scope and target_scope is None:
            await asyncio.to_thread(delete_vectorstore, old_scope)
            kg_store = KGStore()
            try:
                await asyncio.to_thread(kg_store.clear, old_scope)
            finally:
                kg_store.close()

        logger.info("course_material_rebuild_complete", course_id=str(course_id), scope=target_scope)
    except Exception as exc:
        logger.error("course_material_rebuild_failed", course_id=str(course_id), error=str(exc))
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
