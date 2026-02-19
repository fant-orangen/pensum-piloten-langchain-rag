"""Chroma vector store — persistence layer for document embeddings.

Provides two entry-points:
  * ``build_vectorstore`` — used during ingestion to embed and store chunks.
  * ``get_vectorstore``   — used at query time to open the existing store.
"""

import structlog
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import get_settings
from src.vectorstore.embeddings import get_embeddings

logger = structlog.get_logger(__name__)


def get_vectorstore() -> Chroma:
    """Open the persisted Chroma collection (read-only at query time)."""
    settings = get_settings()
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


_EMBED_BATCH_SIZE = 100


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Create (or replace) the Chroma collection from a list of document chunks.

    This is the main write-path called by the ingestion pipeline.
    Chunks are added in batches so progress is visible in the logs.
    """
    settings = get_settings()
    total = len(chunks)
    logger.info("building_vectorstore", num_chunks=total)

    embeddings = get_embeddings()

    # Seed the collection with the first batch, then add the rest incrementally.
    first_batch = chunks[:_EMBED_BATCH_SIZE]
    vectorstore = Chroma.from_documents(
        documents=first_batch,
        embedding=embeddings,
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_dir,
    )
    logger.info("vectorstore_progress", done=len(first_batch), total=total)

    for i in range(_EMBED_BATCH_SIZE, total, _EMBED_BATCH_SIZE):
        batch = chunks[i : i + _EMBED_BATCH_SIZE]
        vectorstore.add_documents(batch)
        logger.info("vectorstore_progress", done=min(i + _EMBED_BATCH_SIZE, total), total=total)

    logger.info("vectorstore_ready", collection=settings.chroma_collection_name)
    return vectorstore
