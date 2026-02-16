from __future__ import annotations

import math
import re
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
from src.ingestion.entities import DOMAIN_TERMS, clean_entities, extract_entities
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
    entity_extractor: str = Field(default="rule")
    spacy_model_name: str = Field(default="en_core_web_sm")
    adaptive_enabled: bool = Field(default=False)
    graph_log: bool = Field(default=False)
    graph_log_top_n: int = Field(default=8)
    graph_log_preview_chars: int = Field(default=120)
    emit_pretty_log: bool = Field(default=True)

    def _chunk_id(self, doc: Document) -> str | None:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id is None:
            source_ref = (
                doc.metadata.get("source_path")
                or doc.metadata.get("source_file")
                or "unknown"
            )
            page = doc.metadata.get("page")
            page_value = str(page) if page is not None else "na"
            chunk_index = doc.metadata.get("chunk_index")
            if chunk_index is None:
                start_index = doc.metadata.get("start_index")
                if start_index is not None:
                    chunk_index = f"s{start_index}"
            if chunk_index is None and source_ref == "unknown":
                return None

            fallback_id = f"{source_ref}::p{page_value}::c{chunk_index if chunk_index is not None else 'na'}"
            doc.metadata["chunk_id"] = fallback_id
            doc.metadata["chunk_id_inferred"] = True
            return fallback_id
        return str(chunk_id)

    def _doc_entities(self, doc: Document) -> list[str]:
        raw = doc.metadata.get("entities")
        if isinstance(raw, list):
            entities = clean_entities(str(e) for e in raw if isinstance(e, str))
            if entities:
                doc.metadata["entities"] = entities
                return entities
        if isinstance(raw, str) and raw.strip():
            parts = clean_entities(part for part in raw.split("|"))
            if parts:
                doc.metadata["entities"] = parts
                return parts

        entities = self._extract_entities(doc.page_content)
        if entities:
            doc.metadata["entities"] = entities
            doc.metadata["entities_inferred"] = True
        return entities

    def _extract_entities(self, text: str, *, max_entities: int = 40) -> list[str]:
        return extract_entities(
            text,
            max_entities=max_entities,
            extractor=self.entity_extractor,
            spacy_model_name=self.spacy_model_name,
        )

    def _adaptive_profile(self, query: str) -> tuple[str, int, int]:
        if not self.adaptive_enabled:
            return "off", self.max_candidates, self.max_entities_per_query

        tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]{1,}", query.lower())
        token_count = len(tokens)
        conceptual_hints = {
            "what",
            "why",
            "how",
            "overview",
            "explain",
            "understand",
            "compare",
            "difference",
            "concept",
        }
        factual_hints = {
            "which",
            "when",
            "where",
            "who",
            "exact",
            "value",
            "size",
            "number",
            "define",
        }
        conceptual_score = sum(1 for token in tokens if token in conceptual_hints)
        factual_score = sum(1 for token in tokens if token in factual_hints)

        if token_count >= 9 or conceptual_score >= 2:
            profile = "broad"
            effective_candidates = min(self.max_candidates + 24, int(self.max_candidates * 1.4))
            effective_entities = min(
                self.max_entities_per_query + 10,
                int(self.max_entities_per_query * 1.4),
            )
        elif token_count <= 5 and factual_score >= 1:
            profile = "narrow"
            effective_candidates = max(self.seed_k, int(self.max_candidates * 0.6))
            effective_entities = max(6, int(self.max_entities_per_query * 0.6))
        else:
            profile = "balanced"
            effective_candidates = self.max_candidates
            effective_entities = self.max_entities_per_query

        return profile, max(self.seed_k, effective_candidates), max(6, effective_entities)

    def _effective_max_df(self) -> int:
        total_chunks = max(1, len(self.graph_index.chunk_entities))
        max_df_cfg = self.max_entity_df
        if max_df_cfg <= 0:
            return total_chunks
        if 0 < max_df_cfg < 1:
            return max(1, int(total_chunks * max_df_cfg))
        return int(max_df_cfg)

    def _select_entities(
        self,
        entity_counter: Counter[str],
        query_entities: set[str],
        *,
        entity_limit: int,
    ) -> list[str]:
        total_chunks = max(1, len(self.graph_index.chunk_entities))
        max_df = self._effective_max_df()
        candidates: list[tuple[str, float]] = []
        normalized_counter: Counter[str] = Counter()

        for entity, count in entity_counter.items():
            cleaned = clean_entities([entity], max_entities=1)
            if not cleaned:
                continue
            normalized_counter[cleaned[0]] += count

        for entity, count in normalized_counter.items():
            df = self.graph_index.entity_df.get(entity, 0)
            if df < self.min_entity_df:
                continue
            tokens = entity.split()
            query_overlap = entity in query_entities or bool(query_entities.intersection(tokens))
            if df > max_df and not query_overlap:
                continue
            if count < 2 and not query_overlap:
                continue

            domain_hits = sum(1 for token in tokens if token in DOMAIN_TERMS)
            idf = min(2.5, math.log((total_chunks + 1) / (df + 1)) + 1.0)
            score = (
                (count * 1.6)
                + (4.0 if query_overlap else 0.0)
                + (domain_hits * 1.0)
                + idf
            )
            if len(tokens) > 1 and domain_hits == 0 and not query_overlap:
                score -= 0.75

            candidates.append((entity, score))
        candidates.sort(key=lambda item: (-item[1], item[0]))
        return [entity for entity, _ in candidates[:entity_limit]]

    def _expand_ids(
        self,
        seed_ids: list[str],
        seed_entities: dict[str, list[str]],
        query_entities: set[str],
        *,
        candidate_limit: int,
        entity_limit: int,
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
            if len(ordered) >= candidate_limit:
                return ordered, []

        selected_entities: list[str] = []
        selected_entity_set: set[str] = set()
        for _ in range(max(1, self.hops)):
            if not frontier or len(ordered) >= candidate_limit:
                break

            entity_counter: Counter[str] = Counter()
            for chunk_id in frontier:
                entities = seed_entities.get(chunk_id) or self.graph_index.chunk_entities.get(chunk_id, [])
                entity_counter.update(entities)

            hop_entities = self._select_entities(
                entity_counter,
                query_entities=query_entities,
                entity_limit=entity_limit,
            )
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
                    if len(ordered) >= candidate_limit:
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
        profile, effective_candidate_limit, effective_entity_limit = self._adaptive_profile(query)
        seed_ids: list[str] = []
        seed_by_id: dict[str, Document] = {}
        seed_entities: dict[str, list[str]] = {}
        inferred_id_count = 0
        inferred_entities_count = 0

        for seed_pos, doc in enumerate(seed_docs):
            chunk_id = self._chunk_id(doc)
            if chunk_id is None:
                chunk_id = f"seed-fallback::{seed_pos}"
                doc.metadata["chunk_id"] = chunk_id
                doc.metadata["chunk_id_inferred"] = True
            if doc.metadata.get("chunk_id_inferred"):
                inferred_id_count += 1

            entities = self._doc_entities(doc)
            if doc.metadata.get("entities_inferred"):
                inferred_entities_count += 1

            if chunk_id not in seed_by_id:
                seed_ids.append(chunk_id)
                seed_by_id[chunk_id] = self._annotate_source(doc, "seed")
            if entities:
                seed_entities[chunk_id] = entities

        if not seed_ids:
            return seed_docs

        if inferred_id_count > 0 or inferred_entities_count > 0:
            logger.warning(
                "seed_metadata_inferred",
                inferred_chunk_ids=inferred_id_count,
                inferred_entities=inferred_entities_count,
                seed_docs=len(seed_docs),
            )

        query_entities = set(self._extract_entities(query, max_entities=20))
        candidate_ids, selected_entities = self._expand_ids(
            seed_ids,
            seed_entities,
            query_entities=query_entities,
            candidate_limit=effective_candidate_limit,
            entity_limit=effective_entity_limit,
        )
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
        if self.graph_log and self.adaptive_enabled:
            logger.info(
                "graph_adaptive_profile",
                profile=profile,
                effective_max_candidates=effective_candidate_limit,
                effective_max_entities=effective_entity_limit,
                query=query[:200],
            )
        graph_debug = {
            "seed_ids": seed_ids[: self.graph_log_top_n],
            "seed_entities": seed_entities_preview,
            "selected_entities": selected_entities[: self.graph_log_top_n],
            "graph_only_ids": graph_only_ids[: self.graph_log_top_n],
            "adaptive_profile": profile,
        }
        for doc in docs:
            doc.metadata["_graph_debug"] = graph_debug

        return docs[:effective_candidate_limit]

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
