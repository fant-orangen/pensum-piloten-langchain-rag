"""Rebuild one course's vector store and KG using the backend ingestion flow.

Usage:
    python -m scripts.ingest_kg
    python -m scripts.ingest_kg --course-code TEST101
"""

import argparse
import asyncio
import sys

import structlog
from sqlalchemy import select

from src.api.database import create_tables, get_session_factory, init_engine
from src.api.models.course import Course
from src.api.services.course_documents import (
    build_course_documents_dir,
    get_course_artifacts_dir,
    run_course_material_rebuild,
    sync_course_documents_from_directory,
)

logger = structlog.get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild a course-scoped vector store and knowledge graph."
    )
    parser.add_argument(
        "--course-code",
        type=str,
        default="TEST101",
        help="Course code to rebuild (defaults to TEST101).",
    )
    args = parser.parse_args(argv)

    asyncio.run(_main_async(args.course_code))


async def _main_async(course_code: str) -> None:
    init_engine()
    await create_tables()

    session_factory = get_session_factory()
    async with session_factory() as db:
        result = await db.execute(select(Course).where(Course.code == course_code))
        course = result.scalars().first()
        if course is None:
            logger.error("course_not_found", course_code=course_code)
            sys.exit(1)

        canonical_documents_dir = build_course_documents_dir(course.code)
        canonical_documents_dir.mkdir(parents=True, exist_ok=True)
        course.documents_dir = str(canonical_documents_dir)
        synced_documents = await sync_course_documents_from_directory(course, db)
        db.add(course)
        await db.commit()

        course_id = course.id
        previous_scope = course.chroma_collection
        previous_version = course.index_version
        documents_dir = course.documents_dir
        artifacts_dir = str(get_course_artifacts_dir(course))

    logger.info(
        "course_rebuild_requested",
        course_code=course_code,
        course_id=str(course_id),
        documents_dir=documents_dir,
        artifacts_dir=artifacts_dir,
        synced_documents=synced_documents,
        previous_scope=previous_scope,
        previous_version=previous_version,
    )
    await run_course_material_rebuild(course_id)

    async with session_factory() as db:
        result = await db.execute(select(Course).where(Course.id == course_id))
        updated_course = result.scalars().first()
        if updated_course is None:
            logger.error("course_missing_after_rebuild", course_code=course_code)
            sys.exit(1)

        if updated_course.rebuild_status == "failed":
            logger.error(
                "course_rebuild_failed",
                course_code=course_code,
                course_id=str(course_id),
                error=updated_course.rebuild_error,
            )
            sys.exit(1)

        logger.info(
            "course_rebuild_complete",
            course_code=course_code,
            course_id=str(course_id),
            documents_dir=updated_course.documents_dir,
            artifacts_dir=str(get_course_artifacts_dir(updated_course)),
            scope=updated_course.chroma_collection,
            index_version=updated_course.index_version,
        )


if __name__ == "__main__":
    main()
