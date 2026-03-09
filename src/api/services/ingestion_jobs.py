"""Background execution of course ingestion jobs."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

import structlog
from sqlalchemy import select

from src.api.database import get_session_factory
from src.api.models.course import Course
from src.api.models.course_ingestion_job import CourseIngestionJob
from src.ingestion import run_kg_ingestion_pipeline

logger = structlog.get_logger(__name__)


async def execute_course_ingestion_job(job_id: uuid.UUID) -> None:
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

        documents_dir = course.documents_dir
        collection_name = course.chroma_collection

    try:
        await asyncio.to_thread(
            run_kg_ingestion_pipeline,
            documents_dir=documents_dir,
            collection_name=collection_name,
            course_scope=collection_name,
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
