"""CrossEncoder reranked retriever.

The retriever keeps the vector store and embedding model fixed, then adds a
second-stage CrossEncoder scorer over a larger candidate pool. This lets us
compare conventional RAG against RAG+reranking without changing chunking,
corpus, or prompt construction.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import structlog
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from src.config import get_settings
from src.vectorstore.store import get_vectorstore

logger = structlog.get_logger(__name__)


class CrossEncoderRerankedRetriever(BaseRetriever):
    """Retrieve vector candidates and rerank them with a CrossEncoder."""

    collection_name: str | None = None
    candidate_k: int = 30
    top_k: int = 5
    cross_encoder_model: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """Return CrossEncoder-reranked chunks for the query."""
        vectorstore = get_vectorstore(self.collection_name)
        candidate_pairs = vectorstore.similarity_search_with_score(query, k=self.candidate_k)
        if not candidate_pairs:
            return []

        reranker = _get_cross_encoder(self.cross_encoder_model)
        rerank_inputs = [(query, document.page_content) for document, _ in candidate_pairs]
        raw_scores = reranker.predict(rerank_inputs)
        scores = [float(score) for score in raw_scores]

        scored_documents = [
            (
                Document(
                    page_content=document.page_content,
                    metadata={
                        **document.metadata,
                        "vector_distance": float(vector_distance),
                        "rerank_score": rerank_score,
                    },
                ),
                rerank_score,
            )
            for (document, vector_distance), rerank_score in zip(candidate_pairs, scores)
        ]
        scored_documents.sort(key=lambda item: item[1], reverse=True)

        final_documents = [document for document, _score in scored_documents[: self.top_k]]
        logger.info(
            "cross_encoder_reranked_retrieval",
            candidates=len(candidate_pairs),
            final_chunks=len(final_documents),
            collection=self.collection_name,
            model=self.cross_encoder_model,
        )
        return final_documents


@lru_cache
def _get_cross_encoder(model_name: str) -> Any:
    """Load and cache the CrossEncoder model on first use."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


def get_reranked_retriever(collection_name: str | None = None) -> CrossEncoderRerankedRetriever:
    """Return a CrossEncoder reranked retriever using configured settings."""
    settings = get_settings()
    return CrossEncoderRerankedRetriever(
        collection_name=collection_name,
        candidate_k=settings.reranker_candidate_k,
        top_k=settings.reranker_top_k,
        cross_encoder_model=settings.cross_encoder_model,
    )
