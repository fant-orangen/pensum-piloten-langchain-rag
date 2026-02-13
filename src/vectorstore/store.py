"""Chroma vector store — persistence layer for document embeddings.

Provides two entry-points:
  * ``build_vectorstore`` — used during ingestion to embed and store chunks.
  * ``get_vectorstore``   — used at query time to open the existing store.
"""

from __future__ import annotations

from collections.abc import Sequence

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


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Create (or replace) the Chroma collection from a list of document chunks.

    This is the main write-path called by the ingestion pipeline.
    """
    settings = get_settings()
    logger.info("building_vectorstore", num_chunks=len(chunks))

    ids: list[str] = []
    store_docs: list[Document] = []
    for i, chunk in enumerate(chunks):
        chunk_id = str(chunk.metadata.get("chunk_id") or f"chunk-{i}")
        chunk.metadata["chunk_id"] = chunk_id
        ids.append(chunk_id)

        metadata = dict(chunk.metadata)
        entities = metadata.get("entities")
        if isinstance(entities, list):
            metadata["entities"] = "|".join(str(entity) for entity in entities if isinstance(entity, str))
        store_docs.append(Document(page_content=chunk.page_content, metadata=metadata))

    vectorstore = Chroma.from_documents(
        documents=store_docs,
        ids=ids,
        embedding=get_embeddings(),
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_dir,
    )

    logger.info("vectorstore_ready", collection=settings.chroma_collection_name)
    return vectorstore


def get_documents_by_ids(vectorstore: object, chunk_ids: Sequence[str]) -> list[Document]:
    """Fetch Documents directly from Chroma by their chunk IDs."""
    if not chunk_ids:
        return []

    payload = vectorstore.get(ids=list(chunk_ids), include=["documents", "metadatas"])  # type: ignore[attr-defined]
    doc_texts = payload.get("documents") or []
    metadatas = payload.get("metadatas") or []
    payload_ids = payload.get("ids") or []

    docs_by_id: dict[str, Document] = {}
    for cid, text, metadata in zip(payload_ids, doc_texts, metadatas):
        doc = Document(page_content=str(text), metadata=dict(metadata or {}))
        if "chunk_id" not in doc.metadata:
            doc.metadata["chunk_id"] = str(cid)
        docs_by_id[str(cid)] = doc

    return [docs_by_id[cid] for cid in chunk_ids if cid in docs_by_id]
