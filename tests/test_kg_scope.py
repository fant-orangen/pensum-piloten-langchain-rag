"""Unit tests for course-scoped KG ingestion/retrieval wiring."""

from langchain_core.documents import Document

from src.kg.extractor import Triplet
from src.kg.retriever import KGExpandedRetriever
import src.ingestion.kg_pipeline as kg_pipeline


class _DummyKGStore:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def get_expanded_subgraph(self, seed_ids: list[str], course_scope: str, hops: int | None = None):
        self.calls.append((seed_ids, course_scope))
        return []


def test_retriever_fetches_subgraph_with_course_scope() -> None:
    kg_store = _DummyKGStore()
    retriever = KGExpandedRetriever(
        kg_store=kg_store,
        top_k=5,
        collection_name="course_collection",
        course_scope="course_scope_1",
    )

    edges = retriever._fetch_subgraph_edges(["chunk_a"])

    assert edges == []
    assert kg_store.calls == [(["chunk_a"], "course_scope_1")]


def test_kg_pipeline_forwards_collection_and_course_scope(monkeypatch) -> None:
    docs = [Document(page_content="Doc", metadata={"source_file": "doc.txt"})]
    chunks = [Document(page_content="Chunk", metadata={"source_file": "doc.txt"})]
    triplets = [Triplet(head="a", relation="b", tail="c", chunk_id="chunk_1")]

    captured: dict[str, str] = {}

    monkeypatch.setattr(kg_pipeline, "load_documents", lambda _directory: docs)
    monkeypatch.setattr(kg_pipeline, "chunk_documents", lambda _docs: chunks)
    monkeypatch.setattr(kg_pipeline, "extract_triplets", lambda _chunks: triplets)

    def _fake_build_vectorstore(_chunks, *, collection_name=None):
        captured["collection_name"] = str(collection_name)
        return object()

    class _FakeKGStore:
        def build_kg(self, _triplets, *, course_scope=None):
            captured["course_scope"] = str(course_scope)

        def close(self):
            return None

    monkeypatch.setattr(kg_pipeline, "build_vectorstore", _fake_build_vectorstore)
    monkeypatch.setattr(kg_pipeline, "KGStore", _FakeKGStore)

    result = kg_pipeline.run_kg_ingestion_pipeline(
        documents_dir="data/documents",
        collection_name="course_collection_2",
        course_scope="course_scope_2",
    )

    assert result["chunks"] == 1
    assert result["triplets"] == 1
    assert captured["collection_name"] == "course_collection_2"
    assert captured["course_scope"] == "course_scope_2"
