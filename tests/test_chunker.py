"""Smoke tests for the chunking module."""

from langchain_core.documents import Document

from src.ingestion.chunker import chunk_documents


def test_chunk_documents_splits_long_text():
    """A document longer than chunk_size should produce multiple chunks."""
    long_text = "word " * 500  # ~2500 characters
    docs = [Document(page_content=long_text, metadata={"source_file": "test.txt"})]

    chunks = chunk_documents(docs)

    assert len(chunks) > 1
    for chunk in chunks:
        assert "source_file" in chunk.metadata
        assert "chunk_index" in chunk.metadata
        assert "chunk_id" in chunk.metadata

    chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))


def test_chunk_documents_preserves_short_text():
    """A document shorter than chunk_size should come through as one chunk."""
    docs = [Document(page_content="Short text.", metadata={"source_file": "test.txt"})]

    chunks = chunk_documents(docs)

    assert len(chunks) == 1
    assert chunks[0].page_content == "Short text."
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[0].metadata["chunk_id"] == "test.txt:c0"
