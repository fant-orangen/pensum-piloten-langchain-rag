"""Vector-only retriever for course-scoped naive RAG."""

import structlog
from langchain_core.retrievers import BaseRetriever

from src.config import get_settings
from src.vectorstore.store import get_vectorstore

logger = structlog.get_logger(__name__)


def get_naive_retriever(collection_name: str | None = None) -> BaseRetriever:
    """Return a plain similarity retriever for one Chroma collection."""
    settings = get_settings()
    vectorstore = get_vectorstore(collection_name)
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.naive_rag_top_k},
    )
    logger.info("naive_retriever_ready", collection=collection_name, top_k=settings.naive_rag_top_k)
    return retriever
