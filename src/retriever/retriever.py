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

from sentence_transformers import CrossEncoder
from src.config import get_settings
from src.vectorstore.store import get_vectorstore
from src.retriever.rerank_retriever import CrossEncoderRerankRetriever

_ce: CrossEncoder | None = None

def get_retriever():
    s = get_settings()
    vectorstore = get_vectorstore()

    # fetch more than you finally use
    base = vectorstore.as_retriever(search_kwargs={"k": s.rerank_fetch_k})


    if not s.rerank_enabled:
        # fall back to normal retrieval
        return vectorstore.as_retriever(search_kwargs={"k": s.retriever_top_k})

    if not getattr(s, "rerank_enabled", False):
        return base

    global _ce
    if _ce is None:
        _ce = CrossEncoder(s.rerank_model_name)

    return CrossEncoderRerankRetriever(
        base_retriever=base,
        cross_encoder=_ce,
        top_k=s.rerank_top_k,
    )