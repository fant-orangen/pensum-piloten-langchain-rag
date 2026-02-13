from __future__ import annotations

from textwrap import shorten

import structlog
from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from src.config import get_settings

logger = structlog.get_logger(__name__)


class CrossEncoderRerankRetriever(BaseRetriever):
    base_retriever: BaseRetriever = Field(...)
    cross_encoder: object = Field(...)
    top_k: int = Field(default=5)

    def _pretty_id(self, doc: Document) -> str:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id:
            return str(chunk_id)
        src = doc.metadata.get("source_file") or doc.metadata.get("source_path") or "unknown"
        page = doc.metadata.get("page")
        return f"{src}" + (f":p{page}" if page is not None else "")

    def _pretty_source(self, doc: Document) -> str:
        source = doc.metadata.get("retrieval_source")
        if source in {"seed", "graph"}:
            return str(source)
        return "base"

    def _log_rerank_debug(
        self,
        query: str,
        docs: list[Document],
        ranked: list[tuple[Document, float]],
    ) -> None:
        settings = get_settings()
        if not (settings.rerank_log or settings.graph_log):
            return

        top_n = min(settings.rerank_log_top_n, len(docs))
        width = settings.rerank_log_preview_chars
        before_positions = {self._pretty_id(doc): pos for pos, doc in enumerate(docs, 1)}

        seed_count = sum(1 for doc in docs if self._pretty_source(doc) == "seed")
        graph_count = sum(1 for doc in docs if self._pretty_source(doc) == "graph")
        graph_debug = next(
            (
                raw
                for raw in (doc.metadata.get("_graph_debug") for doc in docs)
                if isinstance(raw, dict)
            ),
            None,
        )

        logger.info(
            "rerank_debug",
            query=query[:200],
            fetched=len(docs),
            top_k=self.top_k,
            seed_count=seed_count,
            graph_count=graph_count,
        )

        lines = [
            "=" * 70,
            "RETRIEVAL DEBUG",
            f"Query: {query[:120]}",
            f"Fetched: {len(docs)}  Top-k: {self.top_k}  Seed: {seed_count}  Graph: {graph_count}",
        ]
        if isinstance(graph_debug, dict):
            seed_ids = graph_debug.get("seed_ids", [])
            seed_entities = graph_debug.get("seed_entities", [])
            selected_entities = graph_debug.get("selected_entities", [])
            graph_only_ids = graph_debug.get("graph_only_ids", [])
            lines.append("")
            lines.append("--- GRAPH EXPANSION ---")
            lines.append(f"Seed IDs: {', '.join(str(item) for item in seed_ids) or '(none)'}")
            lines.append(
                f"Seed entities: {', '.join(str(item) for item in seed_entities) or '(none)'}"
            )
            lines.append(
                f"Selected entities: {', '.join(str(item) for item in selected_entities) or '(none)'}"
            )
            lines.append(
                f"Graph-only IDs: {', '.join(str(item) for item in graph_only_ids) or '(none)'}"
            )

        lines.append("")
        lines.append("--- BEFORE (candidate order) ---")
        for i, doc in enumerate(docs[:top_n], 1):
            preview = shorten(doc.page_content.replace("\n", " "), width=width, placeholder="…")
            lines.append(
                f"{i:>2}  [{self._pretty_source(doc):<5}] {self._pretty_id(doc):<50} {preview}"
            )

        lines.append("")
        lines.append("--- AFTER (cross-encoder) ---")
        for i, (doc, score) in enumerate(ranked[:top_n], 1):
            preview = shorten(doc.page_content.replace("\n", " "), width=width, placeholder="…")
            lines.append(
                f"{i:>2}  ({score:6.2f}) [{self._pretty_source(doc):<5}] "
                f"{self._pretty_id(doc):<40} {preview}"
            )

        lines.append("")
        lines.append("--- MOVES (final top_k) ---")
        for i, (doc, score) in enumerate(ranked[: self.top_k], 1):
            old_pos = before_positions.get(self._pretty_id(doc), -1)
            lines.append(f"{i:>2}  <- {old_pos:>2}  score={score:6.2f}  {self._pretty_id(doc)}")

        lines.append("=" * 70)
        logger.info("rerank_pretty", message="\n".join(lines))

    def _rerank(self, query: str, docs: list[Document]) -> list[Document]:
        if not docs:
            return docs

        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.cross_encoder.predict(pairs)
        ranked = sorted(
            ((doc, float(score)) for doc, score in zip(docs, scores)),
            key=lambda item: item[1],
            reverse=True,
        )
        self._log_rerank_debug(query=query, docs=docs, ranked=ranked)
        return [doc for doc, _ in ranked[: self.top_k]]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager
        docs = self.base_retriever.invoke(query)
        return self._rerank(query, docs)

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager
        docs = await self.base_retriever.ainvoke(query)
        return self._rerank(query, docs)
