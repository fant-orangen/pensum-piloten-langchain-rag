"""Build the Neo4j knowledge graph from configured source documents.

This script loads documents, chunks them, assigns the same stable chunk IDs used
by the course material rebuild path, extracts triplets, and writes Neo4j.
If a triplets cache file exists, it can reuse that cache to skip LLM extraction.

Usage:
    python -m scripts.build_kg                    # rebuild unscoped KG
    python -m scripts.build_kg --scope COURSE_v1  # rebuild scoped KG
    python -m scripts.build_kg --no-cache         # force triplet extraction
"""

import argparse
import json
import sys
from pathlib import Path

import structlog

from src.config import get_settings
from src.ingestion import load_documents, chunk_documents, make_chunk_id
from src.kg.extractor import extract_triplets, Triplet
from src.kg.store import KGStore

logger = structlog.get_logger(__name__)

_CACHE_DIR = Path(get_settings().chroma_persist_dir).parent
_TRIPLETS_CACHE_NAME = "kg_triplets.json"


def _cache_path(scope: str | None) -> Path:
    """Return the cache path for the requested graph scope."""

    if scope:
        return _CACHE_DIR / f"{scope}_{_TRIPLETS_CACHE_NAME}"
    return _CACHE_DIR / _TRIPLETS_CACHE_NAME


def _save_cache(triplets: list[Triplet], path: Path) -> None:
    """Persist extracted triplets so future KG rebuilds can skip LLM extraction."""

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = [
        {"head": t.head, "relation": t.relation, "tail": t.tail, "chunk_id": t.chunk_id}
        for t in triplets
    ]
    path.write_text(json.dumps(data, ensure_ascii=False))
    logger.info("cache_saved", path=str(path), count=len(triplets))


def _load_cache(path: Path) -> list[Triplet]:
    """Load cached triplets from disk."""

    data = json.loads(path.read_text())
    triplets = [
        Triplet(head=t["head"], relation=t["relation"], tail=t["tail"], chunk_id=t["chunk_id"])
        for t in data
    ]
    logger.info("cache_loaded", path=str(path), count=len(triplets))
    return triplets


def main(argv: list[str] | None = None) -> None:
    """Parse CLI args, obtain triplets, and rebuild the Neo4j graph."""

    parser = argparse.ArgumentParser(
        description="Build Neo4j knowledge graph from cached or re-extracted triplets."
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Force re-extraction from documents instead of using cached triplets.",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default=None,
        help="Neo4j graph scope to rebuild. Defaults to the unscoped graph.",
    )
    args = parser.parse_args(argv)
    cache_path = _cache_path(args.scope)

    if not args.no_cache and cache_path.exists():
        triplets = _load_cache(cache_path)
    else:
        logger.info("step", name="load_documents")
        docs = load_documents()
        if not docs:
            logger.error("no_documents_found")
            sys.exit(1)

        logger.info("step", name="chunk_documents")
        chunks = chunk_documents(docs)

        logger.info("step", name="assign_chunk_ids")
        for chunk in chunks:
            chunk.metadata["chunk_id"] = make_chunk_id(chunk)

        logger.info("step", name="extract_triplets")
        triplets = extract_triplets(chunks)

        _save_cache(triplets, cache_path)

    # Build knowledge graph in Neo4j
    logger.info(
        "step",
        name="build_knowledge_graph",
        triplets=len(triplets),
        scope=args.scope,
    )
    kg_store = KGStore()
    try:
        kg_store.build_kg(triplets, scope=args.scope)
    finally:
        kg_store.close()

    logger.info("kg_build_complete", triplets=len(triplets), scope=args.scope)


if __name__ == "__main__":
    main()
