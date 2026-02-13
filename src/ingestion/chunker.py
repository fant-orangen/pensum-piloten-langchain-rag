"""Text chunking — splits Documents into retrieval-sized pieces.

Uses RecursiveCharacterTextSplitter which is the recommended default for
most document types.  It respects natural boundaries (paragraphs, sentences)
while staying within the configured size limits.
"""

from __future__ import annotations

import structlog
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import get_settings
from src.ingestion.entities import extract_entities

logger = structlog.get_logger(__name__)


def _build_splitter() -> RecursiveCharacterTextSplitter:
    settings = get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        add_start_index=True,          # record byte offset in metadata
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split a list of Documents into smaller chunks for embedding.

    Each resulting chunk inherits the metadata of its parent document and
    gains an additional ``start_index`` field.
    """
    splitter = _build_splitter()
    chunks = splitter.split_documents(documents)

    for chunk_index, chunk in enumerate(chunks):
        source_ref = (
            str(chunk.metadata.get("source_path") or chunk.metadata.get("source_file") or "unknown")
        )
        page = chunk.metadata.get("page")
        page_value = str(page) if page is not None else "na"
        chunk_id = f"{source_ref}::p{page_value}::c{chunk_index}"

        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["chunk_id"] = chunk_id
        chunk.metadata["entities"] = extract_entities(chunk.page_content)

    logger.info(
        "chunking_complete",
        input_docs=len(documents),
        output_chunks=len(chunks),
    )
    return chunks
