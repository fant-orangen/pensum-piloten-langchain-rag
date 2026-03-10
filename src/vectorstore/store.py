"""Chroma vector store — persistence layer for document embeddings.

Provides two entry-points:
  * ``build_vectorstore`` — used during ingestion to embed and store chunks.
  * ``get_vectorstore``   — used at query time to open the existing store.
"""

import chromadb
import structlog
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.config import get_settings
from src.vectorstore.embeddings import get_embeddings

logger = structlog.get_logger(__name__)


def _get_client() -> chromadb.PersistentClient:
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_vectorstore(collection_name: str | None = None) -> Chroma:
    """Open the persisted Chroma collection (read-only at query time).

    If collection_name is provided it must already exist — raises ValueError
    otherwise. This prevents silently querying an empty collection when a
    course has not been ingested yet.
    """
    settings = get_settings()
    name = collection_name or settings.chroma_collection_name

    client = _get_client()  # TODO: should not be used in production
    try:
        client.get_collection(name)
    except Exception:
        raise ValueError(f"Collection '{name}' has not been ingested yet.")

    return Chroma(
        collection_name=name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


_EMBED_BATCH_SIZE = 100


def build_vectorstore(
    chunks: list[Document],
    *,
    collection_name: str | None = None,
    replace: bool = False,
) -> Chroma:
    """Create (or replace) the Chroma collection from a list of document chunks.

    This is the main write-path called by the ingestion pipeline.
    Chunks are added in batches so progress is visible in the logs.
    """
    if not chunks:
        raise ValueError("Cannot build a vectorstore from zero chunks.")

    settings = get_settings()
    name = collection_name or settings.chroma_collection_name
    total = len(chunks)
    logger.info("building_vectorstore", num_chunks=total, collection=name)

    embeddings = get_embeddings()
    client = _get_client()
    if replace:
        try:
            client.delete_collection(name)
        except Exception:
            pass

    # Seed the collection with the first batch, then add the rest incrementally.
    first_batch = chunks[:_EMBED_BATCH_SIZE]
    vectorstore = Chroma.from_documents(
        documents=first_batch,
        embedding=embeddings,
        collection_name=name,
        persist_directory=settings.chroma_persist_dir,
    )
    logger.info("vectorstore_progress", done=len(first_batch), total=total)

    for i in range(_EMBED_BATCH_SIZE, total, _EMBED_BATCH_SIZE):
        batch = chunks[i : i + _EMBED_BATCH_SIZE]
        vectorstore.add_documents(batch)
        logger.info("vectorstore_progress", done=min(i + _EMBED_BATCH_SIZE, total), total=total)

    logger.info("vectorstore_ready", collection=name)
    return vectorstore


def delete_vectorstore(collection_name: str) -> None:
    """Delete a persisted Chroma collection if it exists."""
    client = _get_client()
    try:
        client.delete_collection(collection_name)
        logger.info("vectorstore_deleted", collection=collection_name)
    except Exception:
        logger.info("vectorstore_delete_skipped", collection=collection_name)
