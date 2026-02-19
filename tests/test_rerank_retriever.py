"""Tests for reranker dedupe and chunk-aware identifiers."""

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from src.retriever.rerank_retriever import CrossEncoderRerankRetriever


class _DummyRetriever(BaseRetriever):
    docs: list[Document] = Field(default_factory=list)

    def _get_relevant_documents(self, query: str) -> list[Document]:
        return self.docs

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        return self.docs


class _DummyCrossEncoder:
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]:
        # Deterministic descending preference by original order.
        return [100.0 - i for i in range(len(pairs))]


def test_rerank_dedupes_candidates_by_chunk_id():
    duplicate_a = Document(
        page_content="Same content A",
        metadata={
            "source_file": "vol1.pdf",
            "page": 59,
            "chunk_index": 0,
            "chunk_id": "vol1.pdf:p59:c0",
        },
    )
    duplicate_b = Document(
        page_content="Same content A",
        metadata={
            "source_file": "vol1.pdf",
            "page": 59,
            "chunk_index": 0,
            "chunk_id": "vol1.pdf:p59:c0",
        },
    )
    unique = Document(
        page_content="Different chunk",
        metadata={
            "source_file": "vol1.pdf",
            "page": 59,
            "chunk_index": 1,
            "chunk_id": "vol1.pdf:p59:c1",
        },
    )

    retriever = CrossEncoderRerankRetriever(
        base_retriever=_DummyRetriever(docs=[duplicate_a, duplicate_b, unique]),
        cross_encoder=_DummyCrossEncoder(),
        top_k=5,
    )

    reranked = retriever._get_relevant_documents("memory access")
    reranked_ids = [doc.metadata["chunk_id"] for doc in reranked]

    assert reranked_ids == ["vol1.pdf:p59:c0", "vol1.pdf:p59:c1"]
    assert len(reranked_ids) == len(set(reranked_ids))


def test_pretty_id_includes_chunk_index_when_present():
    retriever = CrossEncoderRerankRetriever(
        base_retriever=_DummyRetriever(docs=[]),
        cross_encoder=_DummyCrossEncoder(),
    )
    doc = Document(
        page_content="x",
        metadata={"source_file": "vol3.pdf", "page": 20, "chunk_index": 3},
    )

    assert retriever._pretty_id(doc) == "vol3.pdf:p20:c3"
