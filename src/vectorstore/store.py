"""Chroma vector store — persistence layer for document embeddings.

Provides two entry-points:
  * ``build_vectorstore`` — used during ingestion to embed and store chunks.
  * ``get_vectorstore``   — used at query time to open the existing store.
"""

import structlog
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import get_settings
from src.document_identity import ensure_chunk_identity
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


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Create (or replace) the Chroma collection from a list of document chunks.

    This is the main write-path called by the ingestion pipeline.
    """
    settings = get_settings()
    deduped_chunks: list[Document] = []
    ids: list[str] = []
    seen_ids: set[str] = set()
    dropped_duplicates = 0

    for i, chunk in enumerate(chunks):
        chunk_id = ensure_chunk_identity(chunk, fallback_chunk_index=i)
        if chunk_id in seen_ids:
            dropped_duplicates += 1
            continue
        seen_ids.add(chunk_id)
        deduped_chunks.append(chunk)
        ids.append(chunk_id)

    logger.info(
        "building_vectorstore",
        num_chunks=len(chunks),
        unique_chunks=len(deduped_chunks),
        dropped_duplicates=dropped_duplicates,
    )

    if deduped_chunks:
        vectorstore = Chroma.from_documents(
            documents=deduped_chunks,
            embedding=get_embeddings(),
            ids=ids,
            collection_name=settings.chroma_collection_name,
            persist_directory=settings.chroma_persist_dir,
        )
    else:
        vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=get_embeddings(),
            persist_directory=settings.chroma_persist_dir,
        )

    logger.info(
        "vectorstore_ready",
        collection=settings.chroma_collection_name,
        stored_chunks=len(deduped_chunks),
    )
    return vectorstore
