"""Chroma vector store — persistence layer for document embeddings.

Provides two entry-points:
  * ``build_vectorstore`` — used during ingestion to embed and store chunks.
  * ``get_vectorstore``   — used at query time to open the existing store.
"""

import structlog
from langchain_community.vectorstores import Chroma
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


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Create (or replace) the Chroma collection from a list of document chunks.

    This is the main write-path called by the ingestion pipeline.
    """
    settings = get_settings()
    logger.info("building_vectorstore", num_chunks=len(chunks))

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_dir,
    )

    logger.info("vectorstore_ready", collection=settings.chroma_collection_name)
    return vectorstore
