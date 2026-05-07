"""Unit tests for course-scoped KG ingestion/retrieval wiring."""

from src.kg.retriever import KGExpandedRetriever


class _DummyKGStore:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str | None]] = []

    def get_expanded_subgraph(
        self,
        seed_ids: list[str],
        scope: str | None = None,
        hops: int | None = None,
    ):
        del hops
        self.calls.append((seed_ids, scope))
        return []


def test_retriever_fetches_subgraph_with_course_scope() -> None:
    kg_store = _DummyKGStore()
    retriever = KGExpandedRetriever(
        kg_store=kg_store,
        top_k=5,
        collection_name="course_collection",
        graph_scope="course_scope_1",
    )

    edges = retriever._fetch_subgraph_edges(["chunk_a"])

    assert edges == []
    assert kg_store.calls == [(["chunk_a"], "course_scope_1")]
