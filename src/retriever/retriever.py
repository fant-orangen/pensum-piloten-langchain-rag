"""Retriever composition.

Default path (both features off):
    vector similarity retriever (k=RETRIEVER_TOP_K)

Optional path:
    vector seed retrieval -> graph expansion -> cross-encoder rerank

Enable via environment variables:
    GRAPH_ENABLED=true
    RERANK_ENABLED=true
"""

from __future__ import annotations

import structlog
from langchain_core.retrievers import BaseRetriever
from sentence_transformers import CrossEncoder

from src.config import get_settings
from src.graph import get_graph_index
from src.retriever.graph_expansion_retriever import GraphExpansionRetriever
from src.retriever.rerank_retriever import CrossEncoderRerankRetriever
from src.vectorstore.store import get_vectorstore

logger = structlog.get_logger(__name__)

_ce: CrossEncoder | None = None


def _seed_k() -> int:
    settings = get_settings()
    if settings.graph_enabled and settings.rerank_enabled:
        return settings.rerank_fetch_k
    if settings.graph_enabled:
        return settings.graph_seed_k
    if settings.rerank_enabled:
        return settings.rerank_fetch_k
    return settings.retriever_top_k


def _get_cross_encoder() -> CrossEncoder:
    settings = get_settings()
    global _ce
    if _ce is None:
        _ce = CrossEncoder(settings.rerank_model_name)
    return _ce


def get_retriever() -> BaseRetriever:
    settings = get_settings()
    vectorstore = get_vectorstore()
    seed_k = _seed_k()

    retriever: BaseRetriever = vectorstore.as_retriever(search_kwargs={"k": seed_k})
    logger.info(
        "retriever_base_configured",
        seed_k=seed_k,
        graph_enabled=settings.graph_enabled,
        rerank_enabled=settings.rerank_enabled,
    )

    if settings.graph_enabled:
        graph_index = get_graph_index(settings.graph_index_path)
        if graph_index is None:
            logger.warning("graph_disabled_runtime", reason="graph_index_missing")
            if not settings.rerank_enabled and seed_k != settings.retriever_top_k:
                retriever = vectorstore.as_retriever(search_kwargs={"k": settings.retriever_top_k})
        else:
            retriever = GraphExpansionRetriever(
                base_retriever=retriever,
                vectorstore=vectorstore,
                graph_index=graph_index,
                seed_k=seed_k,
                max_candidates=settings.graph_max_candidates,
                hops=settings.graph_hops,
                min_entity_df=settings.graph_min_entity_df,
                max_entity_df=settings.graph_max_entity_df,
                max_entities_per_query=settings.graph_max_entities_per_query,
                graph_log=settings.graph_log,
                graph_log_top_n=settings.graph_log_top_n,
                graph_log_preview_chars=settings.graph_log_preview_chars,
                emit_pretty_log=not settings.rerank_enabled,
            )
            logger.info("graph_expansion_enabled", max_candidates=settings.graph_max_candidates)

    if settings.rerank_enabled:
        retriever = CrossEncoderRerankRetriever(
            base_retriever=retriever,
            cross_encoder=_get_cross_encoder(),
            top_k=settings.rerank_top_k or settings.retriever_top_k,
        )
        logger.info("cross_encoder_rerank_enabled", top_k=settings.rerank_top_k)

    return retriever
