"""Ingestion script — loads documents, chunks them, and builds the vector store. Requires a running PostgreSQL instance.

Usage:
    python -m scripts.ingest                      # uses default data/documents/
    python -m scripts.ingest --dir /path/to/docs  # custom directory
    python -m scripts.ingest --collection-name COURSE_v1 --replace
"""

import argparse
import sys

import structlog

from src.ingestion import load_documents, chunk_documents, make_chunk_id
from src.vectorstore import build_vectorstore

logger = structlog.get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    """Load source documents, chunk them, and persist embeddings to Chroma."""

    parser = argparse.ArgumentParser(description="Ingest documents into the vector store.")
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Path to the documents directory (defaults to settings.documents_dir).",
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default=None,
        help="Chroma collection name (defaults to settings.chroma_collection_name).",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete the target Chroma collection before writing new chunks.",
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

    # 3. Assign stable chunk IDs for source resolution.
    logger.info("step", name="assign_chunk_ids")
    for chunk in chunks:
        chunk.metadata["chunk_id"] = make_chunk_id(chunk)

    # 4. Embed & store
    logger.info("step", name="build_vectorstore")
    build_vectorstore(
        chunks,
        collection_name=args.collection_name,
        replace=args.replace,
    )

    logger.info("ingestion_complete", chunks=len(chunks), collection=args.collection_name)


if __name__ == "__main__":
    main()
