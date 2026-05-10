"""Retriever construction — turns the vector store into a LangChain Retriever.

This module is the single place to swap retrieval strategies.  The default is
plain similarity search, but the structure makes it easy to add:
  * Hybrid search  (dense + BM25 sparse)
  * MMR            (Maximal Marginal Relevance for diversity)
  * Contextual compression / reranking
"""

import structlog
from langchain_core.retrievers import BaseRetriever

from src.config import get_settings
from src.vectorstore.store import get_vectorstore

logger = structlog.get_logger(__name__)


def get_retriever(collection_name: str | None = None) -> BaseRetriever:
    """Return a retriever backed by the persisted Chroma vector store.

    Retrieval strategy can be switched here without changing downstream code.
    """
    settings = get_settings()
    vectorstore = get_vectorstore(collection_name)

    # --- Default: similarity search ---
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_top_k},
    )

    # --- Alternative: MMR (uncomment to enable) ---
    # retriever = vectorstore.as_retriever(
    #     search_type="mmr",
    #     search_kwargs={"k": settings.retriever_top_k, "fetch_k": 20},
    # )

    logger.info("retriever_ready", top_k=settings.retriever_top_k, collection=collection_name)
    return retriever
