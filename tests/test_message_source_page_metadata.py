"""Unit tests for backend source page normalization helpers."""

from __future__ import annotations

from types import SimpleNamespace

from src.api.services.message_sources import _source_page
from src.api.services.messages import _serialize_source_documents
from src.api.services.source_metadata import extract_source_page


def test_extract_source_page_reads_aliases_from_source_and_fallback() -> None:
    assert extract_source_page({"page_label": "12"}) == "12"
    assert extract_source_page({"metadata": {"page_number": 7}}) == "7"
    assert extract_source_page({"loc": {"pageNumber": 4}}) == "4"
    assert extract_source_page({}, {"page_num": "9"}) == "9"


def test_source_page_uses_aliases_for_resolution() -> None:
    assert _source_page({"page_label": "Appendix A"}, {}) == "Appendix A"
    assert _source_page({}, {"metadata": {"page_number": 3}}) == "3"
    assert _source_page({"loc": {"pageNumber": 5}}, {}) == "5"
    assert _source_page({}, {}) == ""


def test_serialize_source_documents_persists_alias_page_values() -> None:
    docs = [
        SimpleNamespace(
            metadata={
                "chunk_id": "chunk-1",
                "source_file": "doc-a.pdf",
                "page_label": "12",
            }
        ),
        SimpleNamespace(
            metadata={
                "chunk_id": "chunk-2",
                "source_file": "doc-b.pdf",
                "loc": {"pageNumber": 4},
            }
        ),
    ]

    assert _serialize_source_documents(docs) == [
        {"chunk_id": "chunk-1", "source_file": "doc-a.pdf", "page": "12"},
        {"chunk_id": "chunk-2", "source_file": "doc-b.pdf", "page": "4"},
    ]
