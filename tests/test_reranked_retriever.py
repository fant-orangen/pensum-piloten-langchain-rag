from langchain_core.documents import Document

import src.retriever.reranked_retriever as reranked_retriever
from src.retriever.reranked_retriever import CrossEncoderRerankedRetriever


class _FakeVectorStore:
    def similarity_search_with_score(self, query: str, k: int):
        assert query == "what is paging?"
        assert k == 3
        return [
            (
                Document(
                    page_content="Mostly unrelated text.",
                    metadata={"chunk_id": "chunk_1", "source_file": "a.pdf"},
                ),
                0.1,
            ),
            (
                Document(
                    page_content="Paging maps virtual pages to physical frames.",
                    metadata={"chunk_id": "chunk_2", "source_file": "b.pdf"},
                ),
                0.3,
            ),
            (
                Document(
                    page_content="Some general memory management context.",
                    metadata={"chunk_id": "chunk_3", "source_file": "c.pdf"},
                ),
                0.2,
            ),
        ]


class _FakeCrossEncoder:
    def predict(self, pairs):
        assert [pair[1] for pair in pairs] == [
            "Mostly unrelated text.",
            "Paging maps virtual pages to physical frames.",
            "Some general memory management context.",
        ]
        return [0.2, 0.9, 0.5]


def test_cross_encoder_reranked_retriever_orders_by_rerank_score(monkeypatch) -> None:
    monkeypatch.setattr(reranked_retriever, "get_vectorstore", lambda _collection: _FakeVectorStore())
    monkeypatch.setattr(
        reranked_retriever,
        "_get_cross_encoder",
        lambda _model_name: _FakeCrossEncoder(),
    )

    retriever = CrossEncoderRerankedRetriever(
        collection_name="TEST101_v5",
        candidate_k=3,
        top_k=2,
        cross_encoder_model="fake-cross-encoder",
    )

    docs = retriever._get_relevant_documents("what is paging?", run_manager=None)

    assert [doc.metadata["chunk_id"] for doc in docs] == ["chunk_2", "chunk_3"]
    assert docs[0].metadata["rerank_score"] == 0.9
    assert docs[0].metadata["vector_distance"] == 0.3
