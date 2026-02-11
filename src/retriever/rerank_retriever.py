from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

import structlog
from src.config import get_settings
from textwrap import shorten
from src.config import get_settings

log = structlog.get_logger()


class CrossEncoderRerankRetriever(BaseRetriever):
    base_retriever: BaseRetriever = Field(...)
    cross_encoder: object = Field(...)
    top_k: int = Field(default=5)

    def _pretty_id(self, d):
        src = d.metadata.get("source_file") or d.metadata.get("source_path") or "unknown"
        page = d.metadata.get("page")
        return f"{src}" + (f":p{page}" if page is not None else "")



    
    def _rerank(self, query: str, docs: list[Document]) -> list[Document]:
        if not docs:
            return docs

        s = get_settings()

        pairs = [(query, d.page_content) for d in docs]
        scores = self.cross_encoder.predict(pairs)

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        reranked_docs = [d for d, _ in ranked[: self.top_k]]

        # ---------- PRETTY DEBUG LOG ----------
        if s.rerank_log:
            N = min(s.rerank_log_top_n, len(docs))
            W = s.rerank_log_preview_chars

            before_pos = {self._pretty_id(d): i for i, d in enumerate(docs, 1)}

            print("\n" + "=" * 70)
            print("RERANK DEBUG")
            print(f"Query: {query[:120]}")
            print(f"Fetched: {len(docs)}  →  Top-k: {self.top_k}")

            print("\n--- BEFORE (embedding similarity) ---")
            for i, d in enumerate(docs[:N], 1):
                preview = shorten(d.page_content.replace("\n", " "), width=W, placeholder="…")
                print(f"{i:>2}  {self._pretty_id(d):<30}  {preview}")

            print("\n--- AFTER (cross-encoder) ---")
            for i, (d, sc) in enumerate(ranked[:N], 1):
                preview = shorten(d.page_content.replace("\n", " "), width=W, placeholder="…")
                print(f"{i:>2}  ({sc:6.2f})  {self._pretty_id(d):<30}  {preview}")

            print("\n--- MOVES (final top_k) ---")
            for i, (d, sc) in enumerate(ranked[: self.top_k], 1):
                old = before_pos.get(self._pretty_id(d))
                print(f"{i:>2}  ← {old:>2}   score={sc:6.2f}   {self._pretty_id(d)}")

            print("=" * 70 + "\n")

        return reranked_docs

    def _get_relevant_documents(self, query: str) -> List[Document]:
        docs = self.base_retriever.get_relevant_documents(query)
        return self._rerank(query, docs)

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        docs = await self.base_retriever.aget_relevant_documents(query)
        return self._rerank(query, docs)