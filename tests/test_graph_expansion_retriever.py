from __future__ import annotations

from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from src.graph import build_graph_index
from src.retriever.graph_expansion_retriever import GraphExpansionRetriever


class StaticRetriever(BaseRetriever):
    docs: list[Document] = Field(default_factory=list)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del query, run_manager
        return self.docs

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del query, run_manager
        return self.docs


class FakeVectorstore:
    def __init__(self, docs_by_id: dict[str, Document]) -> None:
        self.docs_by_id = docs_by_id

    def get(self, ids: list[str], include: list[str]) -> dict[str, list[object]]:
        del include
        matched = [cid for cid in ids if cid in self.docs_by_id]
        return {
            "ids": matched,
            "documents": [self.docs_by_id[cid].page_content for cid in matched],
            "metadatas": [self.docs_by_id[cid].metadata for cid in matched],
        }


def _doc(chunk_id: str, entities: list[str], text: str) -> Document:
    return Document(
        page_content=text,
        metadata={
            "chunk_id": chunk_id,
            "entities": entities,
            "source_file": "test.txt",
        },
    )


def test_graph_expansion_adds_related_chunks() -> None:
    d1 = _doc("c1", ["kernel", "system"], "Kernel basics")
    d2 = _doc("c2", ["kernel", "interrupt"], "Interrupt handling in kernel")
    d3 = _doc("c3", ["system", "architecture"], "System architecture overview")
    graph_index = build_graph_index([d1, d2, d3])

    retriever = GraphExpansionRetriever(
        base_retriever=StaticRetriever(docs=[d1]),
        vectorstore=FakeVectorstore({"c2": d2, "c3": d3}),
        graph_index=graph_index,
        seed_k=1,
        max_candidates=5,
        hops=1,
        min_entity_df=1,
        max_entity_df=10,
        max_entities_per_query=10,
    )

    results = retriever.invoke("kernel")
    result_ids = [doc.metadata["chunk_id"] for doc in results]
    assert result_ids == ["c1", "c2", "c3"]


def test_graph_expansion_respects_df_filtering() -> None:
    d1 = _doc("c1", ["kernel", "system"], "Kernel basics")
    d2 = _doc("c2", ["kernel", "interrupt"], "Interrupt handling in kernel")
    d3 = _doc("c3", ["system", "architecture"], "System architecture overview")
    graph_index = build_graph_index([d1, d2, d3])

    retriever = GraphExpansionRetriever(
        base_retriever=StaticRetriever(docs=[d1]),
        vectorstore=FakeVectorstore({"c2": d2, "c3": d3}),
        graph_index=graph_index,
        seed_k=1,
        max_candidates=5,
        hops=1,
        min_entity_df=1,
        max_entity_df=1,
        max_entities_per_query=10,
    )

    results = retriever.invoke("kernel")
    result_ids = [doc.metadata["chunk_id"] for doc in results]
    assert result_ids == ["c1"]


def test_graph_expansion_filters_noisy_non_query_entities() -> None:
    d1 = _doc("c1", ["operating", "systems", "airplanes"], "Operating systems overview")
    d2 = _doc("c2", ["operating", "kernel"], "Kernel interfaces")
    d3 = _doc("c3", ["systems", "scheduler"], "System scheduler")
    d4 = _doc("c4", ["airplanes", "altitude"], "Airplane controls")
    graph_index = build_graph_index([d1, d2, d3, d4])

    retriever = GraphExpansionRetriever(
        base_retriever=StaticRetriever(docs=[d1]),
        vectorstore=FakeVectorstore({"c2": d2, "c3": d3, "c4": d4}),
        graph_index=graph_index,
        seed_k=1,
        max_candidates=5,
        hops=1,
        min_entity_df=1,
        max_entity_df=10,
        max_entities_per_query=10,
    )

    results = retriever.invoke("operating systems")
    selected_entities = results[0].metadata.get("_graph_debug", {}).get("selected_entities", [])
    assert "airplanes" not in selected_entities


def test_graph_expansion_infers_missing_seed_chunk_id() -> None:
    seed = Document(
        page_content="Memory address basics",
        metadata={
            "source_file": "book.pdf",
            "page": 10,
            "entities": ["memory", "address"],
        },
    )
    d2 = _doc("c2", ["memory", "translation"], "Address translation")
    graph_index = build_graph_index(
        [
            Document(
                page_content=seed.page_content,
                metadata={"chunk_id": "book.pdf::p10::c0", "entities": ["memory", "address"]},
            ),
            d2,
        ]
    )

    retriever = GraphExpansionRetriever(
        base_retriever=StaticRetriever(docs=[seed]),
        vectorstore=FakeVectorstore({"c2": d2}),
        graph_index=graph_index,
        seed_k=1,
        max_candidates=5,
        hops=1,
        min_entity_df=1,
        max_entity_df=10,
        max_entities_per_query=10,
    )

    results = retriever.invoke("memory address")
    assert all(doc.metadata.get("chunk_id") is not None for doc in results)
    assert "c2" in [doc.metadata["chunk_id"] for doc in results]


def test_graph_expansion_adaptive_profile_changes_limits() -> None:
    d1 = _doc("c1", ["memory", "address"], "Memory address basics")
    graph_index = build_graph_index([d1])
    retriever = GraphExpansionRetriever(
        base_retriever=StaticRetriever(docs=[d1]),
        vectorstore=FakeVectorstore({}),
        graph_index=graph_index,
        seed_k=1,
        max_candidates=60,
        max_entities_per_query=30,
        adaptive_enabled=True,
    )

    broad = retriever._adaptive_profile(
        "Can you explain and compare virtual memory and physical memory in operating systems?"
    )
    narrow = retriever._adaptive_profile("Which exact address value?")

    assert broad[0] == "broad"
    assert broad[1] >= retriever.max_candidates
    assert narrow[0] == "narrow"
    assert narrow[1] <= retriever.max_candidates
