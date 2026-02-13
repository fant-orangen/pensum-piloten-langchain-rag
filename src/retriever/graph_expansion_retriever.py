from __future__ import annotations

from collections import Counter
from textwrap import shorten

import structlog
from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from src.graph import GraphIndex
from src.ingestion.entities import extract_entities
from src.vectorstore.store import get_documents_by_ids

logger = structlog.get_logger(__name__)


class GraphExpansionRetriever(BaseRetriever):
    """Expand semantically-retrieved seed chunks via an entity-overlap graph."""

    base_retriever: BaseRetriever = Field(...)
    vectorstore: object = Field(...)
    graph_index: GraphIndex = Field(...)
    seed_k: int = Field(default=25)
    max_candidates: int = Field(default=60)
    hops: int = Field(default=1)
    min_entity_df: int = Field(default=2)
    max_entity_df: int = Field(default=200)
    max_entities_per_query: int = Field(default=30)
    graph_log: bool = Field(default=False)
    graph_log_top_n: int = Field(default=8)
    graph_log_preview_chars: int = Field(default=120)
    emit_pretty_log: bool = Field(default=True)

    def _chunk_id(self, doc: Document) -> str | None:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id is None:
            return None
        return str(chunk_id)

    def _doc_entities(self, doc: Document) -> list[str]:
        raw = doc.metadata.get("entities")
        if isinstance(raw, list):
            entities = [str(e).lower() for e in raw if isinstance(e, str) and e.strip()]
            if entities:
                return entities
        if isinstance(raw, str) and raw.strip():
            parts = [part.strip().lower() for part in raw.split("|") if part.strip()]
            if parts:
                doc.metadata["entities"] = parts
                return parts

        logger.warning(
            "entities_missing_in_metadata",
            chunk_id=doc.metadata.get("chunk_id"),
            action="extract_on_the_fly",
        )
        entities = extract_entities(doc.page_content)
        if entities:
            doc.metadata["entities"] = entities
        return entities

    def _select_entities(self, entity_counter: Counter[str]) -> list[str]:
        candidates: list[tuple[str, float]] = []
        for entity, count in entity_counter.items():
            df = self.graph_index.entity_df.get(entity, 0)
            if df < self.min_entity_df or df > self.max_entity_df:
                continue
            score = float(count) / float(df)
            candidates.append((entity, score))
        candidates.sort(key=lambda item: (-item[1], item[0]))
        return [entity for entity, _ in candidates[: self.max_entities_per_query]]

    def _expand_ids(
        self,
        seed_ids: list[str],
        seed_entities: dict[str, list[str]],
    ) -> tuple[list[str], list[str]]:
        seen: set[str] = set()
        ordered: list[str] = []
        frontier: list[str] = []

        for chunk_id in seed_ids:
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            ordered.append(chunk_id)
            frontier.append(chunk_id)
            if len(ordered) >= self.max_candidates:
                return ordered, []

        selected_entities: list[str] = []
        selected_entity_set: set[str] = set()
        for _ in range(max(1, self.hops)):
            if not frontier or len(ordered) >= self.max_candidates:
                break

            entity_counter: Counter[str] = Counter()
            for chunk_id in frontier:
                entities = seed_entities.get(chunk_id) or self.graph_index.chunk_entities.get(chunk_id, [])
                entity_counter.update(entities)

            hop_entities = self._select_entities(entity_counter)
            if not hop_entities:
                break

            for entity in hop_entities:
                if entity not in selected_entity_set:
                    selected_entity_set.add(entity)
                    selected_entities.append(entity)

            new_frontier: list[str] = []
            stop = False
            for entity in hop_entities:
                for candidate_id in self.graph_index.entity_chunks.get(entity, []):
                    if candidate_id in seen:
                        continue
                    seen.add(candidate_id)
                    ordered.append(candidate_id)
                    new_frontier.append(candidate_id)
                    if len(ordered) >= self.max_candidates:
                        stop = True
                        break
                if stop:
                    break

            frontier = new_frontier

        return ordered, selected_entities

    def _annotate_source(self, doc: Document, source: str) -> Document:
        doc.metadata["retrieval_source"] = source
        return doc

    def _preview(self, doc: Document) -> str:
        return shorten(
            doc.page_content.replace("\n", " "),
            width=self.graph_log_preview_chars,
            placeholder="…",
        )

    def _log_graph_debug(
        self,
        query: str,
        seed_ids: list[str],
        seed_entities: list[str],
        entities: list[str],
        candidate_ids: list[str],
        docs_by_id: dict[str, Document],
    ) -> None:
        if not self.graph_log:
            return

        seed_id_set = set(seed_ids)
        graph_only_ids = [cid for cid in candidate_ids if cid not in seed_id_set]
        top_n = self.graph_log_top_n

        seed_preview = seed_ids[:top_n]
        entity_preview = entities[:top_n]
        graph_preview = graph_only_ids[:top_n]

        logger.info(
            "graph_expansion_debug",
            query=query[:200],
            seed_count=len(seed_ids),
            candidate_count=len(candidate_ids),
            graph_only_count=len(graph_only_ids),
            seed_entities=seed_entities[:top_n],
            selected_entities=entity_preview,
            seed_ids=seed_preview,
            graph_only_ids=graph_preview,
        )

        if not self.emit_pretty_log:
            return

        readable = [
            "=" * 70,
            "RETRIEVAL DEBUG",
            f"Query: {query[:120]}",
            f"Seeds: {len(seed_ids)}  Candidates: {len(candidate_ids)}  Graph-only: {len(graph_only_ids)}",
            "",
            "--- SEED IDS ---",
        ]
        readable.extend(seed_preview or ["(none)"])
        readable.append("")
        readable.append("--- SEED ENTITIES ---")
        readable.extend(seed_entities[:top_n] or ["(none)"])
        readable.append("")
        readable.append("--- SELECTED ENTITIES ---")
        readable.extend(entity_preview or ["(none)"])
        readable.append("")
        readable.append("--- GRAPH-ONLY CANDIDATES ---")
        if graph_preview:
            for cid in graph_preview:
                doc = docs_by_id.get(cid)
                if doc is None:
                    readable.append(cid)
                    continue
                readable.append(f"{cid}  {self._preview(doc)}")
        else:
            readable.append("(none)")
        readable.append("=" * 70)
        logger.info("graph_expansion_pretty", message="\n".join(readable))

    def _retrieve(self, query: str, seeds: list[Document]) -> list[Document]:
        seed_docs = seeds[: self.seed_k]
        seed_ids: list[str] = []
        seed_by_id: dict[str, Document] = {}
        seed_entities: dict[str, list[str]] = {}
        seed_without_id: list[Document] = []

        for doc in seed_docs:
            chunk_id = self._chunk_id(doc)
            entities = self._doc_entities(doc)
            if chunk_id is None:
                seed_without_id.append(self._annotate_source(doc, "seed"))
                continue
            if chunk_id not in seed_by_id:
                seed_ids.append(chunk_id)
                seed_by_id[chunk_id] = self._annotate_source(doc, "seed")
            if entities:
                seed_entities[chunk_id] = entities

        if not seed_ids:
            return seed_docs

        candidate_ids, selected_entities = self._expand_ids(seed_ids, seed_entities)
        seed_id_set = set(seed_ids)
        graph_only_ids = [cid for cid in candidate_ids if cid not in seed_id_set]
        graph_docs = get_documents_by_ids(self.vectorstore, graph_only_ids)
        graph_by_id: dict[str, Document] = {}
        for doc in graph_docs:
            chunk_id = self._chunk_id(doc)
            if chunk_id is None:
                continue
            graph_by_id[chunk_id] = self._annotate_source(doc, "graph")

        docs: list[Document] = []
        docs_by_id: dict[str, Document] = {}
        for cid in candidate_ids:
            doc = seed_by_id.get(cid) or graph_by_id.get(cid)
            if doc is None:
                continue
            docs.append(doc)
            docs_by_id[cid] = doc

        docs.extend(seed_without_id)
        seed_entities_preview = [
            entity
            for entity, _ in Counter(
                entity for entities in seed_entities.values() for entity in entities
            ).most_common(self.graph_log_top_n)
        ]

        self._log_graph_debug(
            query=query,
            seed_ids=seed_ids,
            seed_entities=seed_entities_preview,
            entities=selected_entities,
            candidate_ids=candidate_ids,
            docs_by_id=docs_by_id,
        )
        graph_debug = {
            "seed_ids": seed_ids[: self.graph_log_top_n],
            "seed_entities": seed_entities_preview,
            "selected_entities": selected_entities[: self.graph_log_top_n],
            "graph_only_ids": graph_only_ids[: self.graph_log_top_n],
        }
        for doc in docs:
            doc.metadata["_graph_debug"] = graph_debug

        return docs[: self.max_candidates]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager
        seeds = self.base_retriever.invoke(query)
        return self._retrieve(query, seeds)

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager
        seeds = await self.base_retriever.ainvoke(query)
        return self._retrieve(query, seeds)
