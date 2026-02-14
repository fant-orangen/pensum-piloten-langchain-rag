"""KG ingestion script — loads documents, chunks them, builds the vector store,
extracts triplets, and populates the Neo4j knowledge graph.

Usage:
    python -m scripts.ingest_kg                      # uses default data/documents/
    python -m scripts.ingest_kg --dir /path/to/docs  # custom directory
"""

import argparse
import sys

import structlog

from src.ingestion import load_documents, chunk_documents
from src.kg.extractor import extract_triplets, make_chunk_id
from src.kg.store import KGStore
from src.vectorstore import build_vectorstore

logger = structlog.get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Ingest documents into vector store and build knowledge graph."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to the documents directory (defaults to settings.documents_dir).",
    )
    args = parser.parse_args(argv)

    # 1. Load
    logger.info("step", name="load_documents")
    docs = load_documents(args.dir)
    if not docs:
        logger.error("no_documents_found")
        sys.exit(1)

    # 2. Chunk
    logger.info("step", name="chunk_documents")
    chunks = chunk_documents(docs)

    # 3. Assign stable chunk IDs (needed to link ChromaDB <-> Neo4j)
    logger.info("step", name="assign_chunk_ids")
    for chunk in chunks:
        chunk.metadata["chunk_id"] = make_chunk_id(chunk)

    # 4. Embed & store in ChromaDB (with chunk_id metadata)
    logger.info("step", name="build_vectorstore")
    build_vectorstore(chunks)

    # 5. Extract triplets from chunks via LLM
    logger.info("step", name="extract_triplets")
    triplets = extract_triplets(chunks)

    # 6. Build knowledge graph in Neo4j
    logger.info("step", name="build_knowledge_graph")
    chunk_metadata = {
        chunk.metadata["chunk_id"]: {
            "source_file": chunk.metadata.get("source_file", "unknown"),
            "page": chunk.metadata.get("page", ""),
        }
        for chunk in chunks
    }

    kg_store = KGStore()
    try:
        kg_store.build_kg(triplets, chunk_metadata)
    finally:
        kg_store.close()

    logger.info(
        "kg_ingestion_complete",
        chunks=len(chunks),
        triplets=len(triplets),
    )


if __name__ == "__main__":
    main()
