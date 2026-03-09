"""Background execution of course ingestion jobs."""

from __future__ import annotations

import asyncio
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import structlog
from sqlalchemy import select

from src.api.database import get_session_factory
from src.api.models.course import Course
from src.api.models.course_ingestion_job import CourseIngestionJob
from src.api.models.course_material import CourseMaterial
from src.ingestion import run_kg_ingestion_pipeline

logger = structlog.get_logger(__name__)


def _run_pipeline_with_staged_materials(
    materials: list[CourseMaterial],
    *,
    collection_name: str,
) -> dict[str, int]:
    selected_count = len(materials)
    with tempfile.TemporaryDirectory(prefix=f"course_ingest_{collection_name}_") as temp_dir:
        staging_root = Path(temp_dir)
        usable_count = 0
        missing_count = 0
        for material in materials:
            source_path = Path(material.storage_path)
            if not source_path.exists() or not source_path.is_file():
                missing_count += 1
                continue
            if source_path.stat().st_size <= 0:
                continue

            clean_name = Path(material.original_filename or source_path.name).name
            target_name = f"{material.id}_{clean_name or source_path.name}"
            target_path = staging_root / target_name
            shutil.copy2(source_path, target_path)
            usable_count += 1

        if usable_count == 0:
            raise ValueError(
                "No readable material files found for ingestion "
                f"(selected={selected_count}, usable={usable_count}, missing={missing_count})."
            )

        return run_kg_ingestion_pipeline(
            documents_dir=staging_root,
            collection_name=collection_name,
            course_scope=collection_name,
        )


async def execute_course_ingestion_job(
    job_id: uuid.UUID,
    material_ids: list[uuid.UUID] | None = None,
) -> None:
    """Run one queued ingestion job and persist final status."""
    session_factory = get_session_factory()

    async with session_factory() as db:
        result = await db.execute(select(CourseIngestionJob).where(CourseIngestionJob.id == job_id))
        job = result.scalars().first()
        if job is None:
            logger.warning("ingestion_job_missing", job_id=str(job_id))
            return
        if job.status != "queued":
            logger.info("ingestion_job_skipped", job_id=str(job_id), status=job.status)
            return

        course_result = await db.execute(select(Course).where(Course.id == job.course_id))
        course = course_result.scalars().first()
        if course is None:
            job.status = "failed"
            job.error_message = "Course not found."
            job.finished_at = datetime.utcnow()
            db.add(job)
            await db.commit()
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.error_message = None
        db.add(job)
        await db.commit()

        collection_name = course.chroma_collection
        selected_ids = list(material_ids or [])

        preflight_error: str | None = None

        if selected_ids:
            materials_result = await db.execute(
                select(CourseMaterial).where(
                    CourseMaterial.course_id == course.id,
                    CourseMaterial.id.in_(selected_ids),
                )
            )
            material_rows = list(materials_result.scalars().all())
            materials_by_id = {item.id: item for item in material_rows}
            missing_ids = [item for item in selected_ids if item not in materials_by_id]
            if missing_ids:
                preflight_error = (
                    "Selected materials are no longer available for this course "
                    f"(selected={len(selected_ids)}, found={len(material_rows)})."
                )
            selected_materials = [materials_by_id[item] for item in selected_ids if item in materials_by_id]
        else:
            materials_result = await db.execute(
                select(CourseMaterial)
                .where(CourseMaterial.course_id == course.id)
                .order_by(CourseMaterial.created_at.asc())
            )
            selected_materials = list(materials_result.scalars().all())
            if not selected_materials:
                preflight_error = "No uploaded materials found for this course."

    try:
        if preflight_error:
            raise ValueError(preflight_error)
        await asyncio.to_thread(
            _run_pipeline_with_staged_materials,
            selected_materials,
            collection_name=collection_name,
        )
    except Exception as exc:
        logger.exception("ingestion_job_failed", job_id=str(job_id))
        async with session_factory() as db:
            result = await db.execute(select(CourseIngestionJob).where(CourseIngestionJob.id == job_id))
            job = result.scalars().first()
            if job is not None:
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.utcnow()
                db.add(job)
                await db.commit()
        return

    async with session_factory() as db:
        result = await db.execute(select(CourseIngestionJob).where(CourseIngestionJob.id == job_id))
        job = result.scalars().first()
        if job is not None:
            job.status = "completed"
            job.finished_at = datetime.utcnow()
            job.error_message = None
            db.add(job)
            await db.commit()
