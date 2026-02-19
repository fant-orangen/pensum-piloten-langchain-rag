from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from textwrap import shorten

from src.config import get_settings
from src.document_identity import (
    document_debug_fields,
    document_dedupe_key,
    document_page,
    document_source,
)


class CrossEncoderRerankRetriever(BaseRetriever):
    base_retriever: BaseRetriever = Field(...)
    cross_encoder: object = Field(...)
    top_k: int = Field(default=5)

    def _pretty_id(self, doc: Document) -> str:
        source = doc.metadata.get("source_file") or document_source(doc.metadata)
        page = document_page(doc.metadata)
        chunk_index = doc.metadata.get("chunk_index")

        label = f"{source}" + (f":p{page}" if page is not None else "")
        if chunk_index is not None:
            label += f":c{chunk_index}"
        return label

    def _dedupe_docs(self, docs: list[Document]) -> tuple[list[Document], int]:
        """Deduplicate by stable key while preserving first occurrence order."""
        unique_docs: list[Document] = []
        seen_keys: set[str] = set()
        dropped = 0
        for doc in docs:
            key = document_dedupe_key(doc)
            if key in seen_keys:
                dropped += 1
                continue
            seen_keys.add(key)
            unique_docs.append(doc)
        return unique_docs, dropped

    def _rerank(self, query: str, docs: list[Document]) -> list[Document]:
        if not docs:
            return docs

        s = get_settings()
        raw_count = len(docs)
        docs, dropped_before = self._dedupe_docs(docs)

        pairs = [(query, d.page_content) for d in docs]
        scores = self.cross_encoder.predict(pairs)

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        ranked_unique: list[tuple[Document, float]] = []
        seen_ranked: set[str] = set()
        dropped_after = 0
        for doc, score in ranked:
            key = document_dedupe_key(doc)
            if key in seen_ranked:
                dropped_after += 1
                continue
            seen_ranked.add(key)
            ranked_unique.append((doc, float(score)))

        reranked_docs = [d for d, _ in ranked_unique[: self.top_k]]

        # ---------- PRETTY DEBUG LOG ----------
        if s.rerank_log:
            N = min(s.rerank_log_top_n, len(docs))
            W = s.rerank_log_preview_chars

            before_pos: dict[str, int] = {}
            for i, d in enumerate(docs, 1):
                key = document_dedupe_key(d)
                if key not in before_pos:
                    before_pos[key] = i

            print("\n" + "=" * 70)
            print("RERANK DEBUG")
            print(f"Query: {query[:120]}")
            fetched_line = (
                f"Fetched: {raw_count}  →  "
                f"Unique candidates: {len(docs)}  →  "
                f"Top-k: {self.top_k}"
            )
            print(fetched_line)
            if dropped_before:
                print(f"Dropped before scoring (duplicate chunk keys): {dropped_before}")
            if dropped_after:
                print(f"Dropped after scoring (safety dedupe): {dropped_after}")

            print("\n--- BEFORE (embedding similarity) ---")
            for i, d in enumerate(docs[:N], 1):
                preview = shorten(d.page_content.replace("\n", " "), width=W, placeholder="…")
                dbg = document_debug_fields(d)
                print(
                    f"{i:>2}  {self._pretty_id(d):<36}  "
                    f"id={dbg['chunk_id']:<24} "
                    f"hash={dbg['content_hash']}  {preview}"
                )

            print("\n--- AFTER (cross-encoder) ---")
            for i, (d, sc) in enumerate(ranked_unique[:N], 1):
                preview = shorten(d.page_content.replace("\n", " "), width=W, placeholder="…")
                dbg = document_debug_fields(d)
                print(
                    f"{i:>2}  ({sc:6.2f})  {self._pretty_id(d):<36}  "
                    f"id={dbg['chunk_id']:<24} "
                    f"hash={dbg['content_hash']}  {preview}"
                )

            print("\n--- MOVES (final top_k) ---")
            for i, (d, sc) in enumerate(ranked_unique[: self.top_k], 1):
                key = document_dedupe_key(d)
                old = before_pos.get(key)
                old_pos = f"{old:>2}" if old is not None else " -"
                print(f"{i:>2}  ← {old_pos}   score={sc:6.2f}   {self._pretty_id(d)}")

            print("=" * 70 + "\n")

        return reranked_docs

    def _get_relevant_documents(self, query: str) -> List[Document]:
        docs = list(self.base_retriever.invoke(query))
        return self._rerank(query, docs)

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        docs = list(await self.base_retriever.ainvoke(query))
        return self._rerank(query, docs)
