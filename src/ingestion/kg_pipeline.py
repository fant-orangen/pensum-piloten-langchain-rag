"""Reusable KG ingestion pipeline used by API jobs and CLI scripts."""

from pathlib import Path

import json
import structlog

from src.ingestion import chunk_documents, load_documents
from src.kg.extractor import Triplet, extract_triplets, make_chunk_id
from src.kg.store import KGStore
from src.vectorstore import build_vectorstore

logger = structlog.get_logger(__name__)


def _save_triplets_cache(path: Path, triplets: list[Triplet]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {"head": t.head, "relation": t.relation, "tail": t.tail, "chunk_id": t.chunk_id}
        for t in triplets
    ]
    path.write_text(json.dumps(data, ensure_ascii=False))
    logger.info("triplets_cached", path=str(path), count=len(triplets))


def run_kg_ingestion_pipeline(
    *,
    documents_dir: str | Path | None = None,
    triplets_cache_path: str | Path | None = None,
) -> dict[str, int]:
    """Run the full KG ingestion flow.

    Flow:
    1) load documents
    2) chunk documents
    3) assign stable chunk IDs
    4) build vector store
    5) extract triplets
    6) build Neo4j KG
    """
    logger.info("step", name="load_documents")
    docs = load_documents(documents_dir)
    if not docs:
        raise ValueError("No documents found for ingestion.")

    logger.info("step", name="chunk_documents")
    chunks = chunk_documents(docs)

    logger.info("step", name="assign_chunk_ids")
    for chunk in chunks:
        chunk.metadata["chunk_id"] = make_chunk_id(chunk)

    logger.info("step", name="build_vectorstore")
    build_vectorstore(chunks)

    logger.info("step", name="extract_triplets")
    triplets = extract_triplets(chunks)

    if triplets_cache_path:
        _save_triplets_cache(Path(triplets_cache_path), triplets)

    logger.info("step", name="build_knowledge_graph")
    kg_store = KGStore()
    try:
        kg_store.build_kg(triplets)
    finally:
        kg_store.close()

    logger.info(
        "kg_ingestion_complete",
        chunks=len(chunks),
        triplets=len(triplets),
    )
    return {"chunks": len(chunks), "triplets": len(triplets)}
