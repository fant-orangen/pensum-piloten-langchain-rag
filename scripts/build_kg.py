"""Build the Neo4j knowledge graph from an already-ingested vectorstore.

Assumes that `python -m scripts.ingest_kg` (or at least steps 1-5) has already run,
so chunks with chunk_ids exist in ChromaDB and triplets can be re-extracted from
the stored chunks. This script re-extracts triplets and builds the KG without
re-embedding.

However, if a triplets cache file exists, it will use that directly to avoid
the expensive LLM extraction step.

Usage:
    python -m scripts.build_kg                # rebuild KG (uses cache if available)
    python -m scripts.build_kg --no-cache     # force re-extraction from chunks
"""

import argparse
import json
import sys
from pathlib import Path

import structlog

from src.config import get_settings
from src.ingestion import load_documents, chunk_documents
from src.kg.extractor import extract_triplets, make_chunk_id, Triplet
from src.kg.store import KGStore

logger = structlog.get_logger(__name__)

_CACHE_DIR = Path(get_settings().chroma_persist_dir).parent
_TRIPLETS_CACHE = _CACHE_DIR / "kg_triplets.json"


def _save_cache(triplets: list[Triplet]) -> None:
    """Persist extracted triplets so future KG rebuilds can skip LLM extraction."""

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data = [
        {"head": t.head, "relation": t.relation, "tail": t.tail, "chunk_id": t.chunk_id}
        for t in triplets
    ]
    _TRIPLETS_CACHE.write_text(json.dumps(data, ensure_ascii=False))
    logger.info("cache_saved", path=str(_TRIPLETS_CACHE), count=len(triplets))


def _load_cache() -> list[Triplet]:
    """Load cached triplets from disk."""

    data = json.loads(_TRIPLETS_CACHE.read_text())
    triplets = [
        Triplet(head=t["head"], relation=t["relation"], tail=t["tail"], chunk_id=t["chunk_id"])
        for t in data
    ]
    logger.info("cache_loaded", path=str(_TRIPLETS_CACHE), count=len(triplets))
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
    args = parser.parse_args(argv)

    if not args.no_cache and _TRIPLETS_CACHE.exists():
        triplets = _load_cache()
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

        _save_cache(triplets)

    # Build knowledge graph in Neo4j
    logger.info("step", name="build_knowledge_graph", triplets=len(triplets))
    kg_store = KGStore()
    try:
        kg_store.build_kg(triplets)
    finally:
        kg_store.close()

    logger.info("kg_build_complete", triplets=len(triplets))


if __name__ == "__main__":
    main()
