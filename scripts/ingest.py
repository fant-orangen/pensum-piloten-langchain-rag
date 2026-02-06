"""Ingestion script — loads documents, chunks them, and builds the vector store.

Usage:
    python -m scripts.ingest                      # uses default data/documents/
    python -m scripts.ingest --dir /path/to/docs  # custom directory
"""

import argparse
import sys

import structlog

from src.ingestion import load_documents, chunk_documents
from src.vectorstore import build_vectorstore

logger = structlog.get_logger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into the vector store.")
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

    # 3. Embed & store
    logger.info("step", name="build_vectorstore")
    build_vectorstore(chunks)

    logger.info("ingestion_complete", chunks=len(chunks))


if __name__ == "__main__":
    main()
