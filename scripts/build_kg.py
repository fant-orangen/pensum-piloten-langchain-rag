"""Replay cached per-course KG triplets into Neo4j.

For each course that has a `rebuild_manifest.json` + `kg_triplets.json` on disk
(produced by `run_course_material_rebuild`), this reads the triplets and writes
them into Neo4j under the scope recorded in the manifest. No LLM calls, no
document loading, no ChromaDB changes — pure graph upsert.

Designed to be both:
- a CLI tool: ``python -m scripts.build_kg [--course-code CODE] [--force]``
- a library: import ``load_all_courses`` / ``load_course`` from other modules
  (e.g. FastAPI startup) to bootstrap a fresh Neo4j volume from artifacts.

Idempotent by default: if a scope already has edges in Neo4j, it is skipped.
Pass ``--force`` to repopulate regardless.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import structlog

from src.api.services.course_documents import (
    COURSE_ARTIFACTS_DIRNAME,
    build_course_documents_dir,
)
from src.config import get_settings
from src.kg.extractor import Triplet
from src.kg.store import KGStore

logger = structlog.get_logger(__name__)

MANIFEST_FILENAME = "rebuild_manifest.json"
TRIPLETS_FILENAME = "kg_triplets.json"


@dataclass(frozen=True)
class LoadResult:
    """Outcome of loading one course's cached triplets."""

    course_code: str
    scope: str | None
    triplet_count: int
    status: str  # "loaded" | "skipped_present" | "skipped_missing" | "failed"
    detail: str | None = None


def _artifacts_dir_for(course_code: str) -> Path:
    """Return the per-course artifacts directory (may not exist)."""
    return build_course_documents_dir(course_code) / COURSE_ARTIFACTS_DIRNAME


def _read_manifest(artifacts_dir: Path) -> dict | None:
    """Parse rebuild_manifest.json; return None if missing or unreadable."""
    path = artifacts_dir / MANIFEST_FILENAME
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("manifest_unreadable", path=str(path), error=str(exc))
        return None
    return payload if isinstance(payload, dict) else None


def _read_triplets(artifacts_dir: Path) -> list[Triplet]:
    """Parse kg_triplets.json into a list of Triplet objects."""
    path = artifacts_dir / TRIPLETS_FILENAME
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        Triplet(
            head=item["head"],
            relation=item["relation"],
            tail=item["tail"],
            chunk_id=item["chunk_id"],
        )
        for item in raw
    ]


def _scope_has_edges(kg: KGStore, scope: str) -> bool:
    """Check whether Neo4j already has at least one RELATED_TO edge for a scope."""
    with kg._driver.session() as session:
        record = session.run(
            "MATCH ()-[r:RELATED_TO {scope: $scope}]->() RETURN count(r) AS cnt",
            scope=scope,
        ).single()
    return bool(record and record["cnt"] > 0)


def discover_course_codes() -> list[str]:
    """Return all course codes that have a rebuild manifest on disk."""
    root = Path(get_settings().documents_dir)
    if not root.exists():
        return []
    codes: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if (child / COURSE_ARTIFACTS_DIRNAME / MANIFEST_FILENAME).exists():
            codes.append(child.name)
    return codes


def load_course(
    course_code: str,
    *,
    kg: KGStore | None = None,
    force: bool = False,
) -> LoadResult:
    """Load one course's cached triplets into Neo4j.

    Args:
        course_code: Course folder name under ``settings.documents_dir``.
        kg: Optional KGStore to reuse across calls. A new one is created and
            closed internally when omitted.
        force: Rebuild the scope even if Neo4j already has edges for it.

    Returns:
        A ``LoadResult`` describing what happened.
    """
    artifacts_dir = _artifacts_dir_for(course_code)
    manifest = _read_manifest(artifacts_dir)
    if manifest is None:
        logger.info("kg_load_skipped", course_code=course_code, reason="no_manifest")
        return LoadResult(course_code, None, 0, "skipped_missing", "no manifest")

    scope = manifest.get("scope")
    if not isinstance(scope, str) or not scope.strip():
        logger.warning("kg_load_skipped", course_code=course_code, reason="no_scope")
        return LoadResult(course_code, None, 0, "skipped_missing", "manifest has no scope")
    scope = scope.strip()

    triplets_path = artifacts_dir / TRIPLETS_FILENAME
    if not triplets_path.exists():
        logger.info(
            "kg_load_skipped",
            course_code=course_code,
            scope=scope,
            reason="no_triplets_file",
        )
        return LoadResult(course_code, scope, 0, "skipped_missing", "no triplets file")

    owns_kg = kg is None
    kg = kg or KGStore()
    try:
        if not force and _scope_has_edges(kg, scope):
            logger.info(
                "kg_load_skipped",
                course_code=course_code,
                scope=scope,
                reason="scope_already_populated",
            )
            return LoadResult(course_code, scope, 0, "skipped_present", "scope already has edges")

        triplets = _read_triplets(artifacts_dir)
        logger.info(
            "kg_load_started",
            course_code=course_code,
            scope=scope,
            triplet_count=len(triplets),
            force=force,
        )
        kg.build_kg(triplets, scope=scope)
        logger.info(
            "kg_load_complete",
            course_code=course_code,
            scope=scope,
            triplet_count=len(triplets),
        )
        return LoadResult(course_code, scope, len(triplets), "loaded")
    finally:
        if owns_kg:
            kg.close()


def load_all_courses(
    *,
    course_codes: Iterable[str] | None = None,
    force: bool = False,
) -> list[LoadResult]:
    """Load cached triplets for multiple courses, reusing one Neo4j session.

    Args:
        course_codes: Optional iterable of course codes. If None, every course
            folder with a manifest on disk is processed.
        force: Rebuild every scope regardless of current Neo4j state.

    Returns:
        A list of ``LoadResult`` values, one per processed course. Failures
        are captured as ``status="failed"`` results; this function does not
        raise on per-course errors, so callers can decide how to react.
    """
    codes = list(course_codes) if course_codes is not None else discover_course_codes()
    if not codes:
        logger.info("kg_load_no_courses")
        return []

    results: list[LoadResult] = []
    kg = KGStore()
    try:
        for code in codes:
            try:
                results.append(load_course(code, kg=kg, force=force))
            except Exception as exc:
                logger.exception("kg_load_failed", course_code=code, error=str(exc))
                results.append(LoadResult(code, None, 0, "failed", str(exc)))
    finally:
        kg.close()

    return results


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay cached KG triplets into Neo4j for one or all courses. "
            "No LLM calls. Safe and idempotent — running again is a no-op "
            "unless --force is supplied or a scope has been wiped."
        ),
    )
    parser.add_argument(
        "--course-code",
        type=str,
        default=None,
        help=(
            "Course folder name to populate (e.g. os_g1). "
            "If omitted, every course folder with a manifest is processed."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild the scope in Neo4j even if it already contains edges.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    codes = [args.course_code] if args.course_code else None
    results = load_all_courses(course_codes=codes, force=args.force)

    for result in results:
        logger.info(
            "kg_load_result",
            course_code=result.course_code,
            scope=result.scope,
            status=result.status,
            triplet_count=result.triplet_count,
            detail=result.detail,
        )

    failed = [r for r in results if r.status == "failed"]
    if failed and args.course_code:
        sys.exit(1)


if __name__ == "__main__":
    main()
