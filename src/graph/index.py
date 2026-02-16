"""Lightweight persisted graph index for graph-guided retrieval."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import structlog
from langchain_core.documents import Document

from src.config import get_settings
from src.ingestion.entities import clean_entities, extract_entities

logger = structlog.get_logger(__name__)

_GRAPH_INDEX_CACHE: dict[str, "GraphIndex"] = {}


@dataclass(slots=True)
class GraphIndex:
    chunk_entities: dict[str, list[str]]
    entity_chunks: dict[str, list[str]]
    entity_df: dict[str, int]

    def to_dict(self) -> dict[str, dict[str, list[str]] | dict[str, int]]:
        return {
            "chunk_entities": self.chunk_entities,
            "entity_chunks": self.entity_chunks,
            "entity_df": self.entity_df,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "GraphIndex":
        raw_chunk_entities = payload.get("chunk_entities")
        raw_entity_chunks = payload.get("entity_chunks")
        raw_entity_df = payload.get("entity_df")

        chunk_entities_items = raw_chunk_entities.items() if isinstance(raw_chunk_entities, dict) else []
        entity_chunks_items = raw_entity_chunks.items() if isinstance(raw_entity_chunks, dict) else []
        entity_df_items = raw_entity_df.items() if isinstance(raw_entity_df, dict) else []

        chunk_entities = {
            str(k): sorted({str(v) for v in values})
            for k, values in chunk_entities_items
            if isinstance(values, list)
        }
        entity_chunks = {
            str(k): sorted({str(v) for v in values})
            for k, values in entity_chunks_items
            if isinstance(values, list)
        }
        entity_df = {str(k): int(v) for k, v in entity_df_items}
        return cls(
            chunk_entities=chunk_entities,
            entity_chunks=entity_chunks,
            entity_df=entity_df,
        )


def build_graph_index(chunks: list[Document]) -> GraphIndex:
    """Build a cheap overlap graph from chunk entities."""
    settings = get_settings()
    chunk_entities: dict[str, list[str]] = {}
    entity_chunks_map: dict[str, set[str]] = defaultdict(set)

    for i, chunk in enumerate(chunks):
        chunk_id = str(chunk.metadata.get("chunk_id") or f"chunk-{i}")
        entities_raw = chunk.metadata.get("entities")
        if isinstance(entities_raw, list):
            entities = clean_entities(str(e) for e in entities_raw if isinstance(e, str))
        else:
            entities = extract_entities(
                chunk.page_content,
                extractor=settings.graph_entity_extractor,
                spacy_model_name=settings.graph_spacy_model_name,
            )

        unique_entities = sorted(set(entities))
        chunk_entities[chunk_id] = unique_entities
        for entity in unique_entities:
            entity_chunks_map[entity].add(chunk_id)

    entity_chunks = {entity: sorted(chunk_ids) for entity, chunk_ids in entity_chunks_map.items()}
    entity_df = {entity: len(chunk_ids) for entity, chunk_ids in entity_chunks.items()}

    index = GraphIndex(
        chunk_entities=chunk_entities,
        entity_chunks=entity_chunks,
        entity_df=entity_df,
    )
    logger.info(
        "graph_index_built",
        chunks=len(chunk_entities),
        entities=len(entity_chunks),
    )
    return index


def persist_graph_index(index: GraphIndex, path: str | Path | None = None) -> Path:
    settings = get_settings()
    out_path = Path(path) if path else Path(settings.graph_index_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index.to_dict(), ensure_ascii=True), encoding="utf-8")
    _GRAPH_INDEX_CACHE[str(out_path.resolve())] = index
    logger.info("graph_index_persisted", path=str(out_path))
    return out_path


def load_graph_index(path: str | Path | None = None) -> GraphIndex:
    settings = get_settings()
    in_path = Path(path) if path else Path(settings.graph_index_path)
    payload = json.loads(in_path.read_text(encoding="utf-8"))
    index = GraphIndex.from_dict(payload)
    logger.info(
        "graph_index_loaded",
        path=str(in_path),
        chunks=len(index.chunk_entities),
        entities=len(index.entity_chunks),
    )
    return index


def get_graph_index(path: str | Path | None = None, *, force_reload: bool = False) -> GraphIndex | None:
    """Load and cache the graph index lazily for query-time retrieval."""
    settings = get_settings()
    in_path = (Path(path) if path else Path(settings.graph_index_path)).resolve()
    if not in_path.exists():
        logger.warning("graph_index_missing", path=str(in_path))
        return None

    key = str(in_path)
    if not force_reload and key in _GRAPH_INDEX_CACHE:
        return _GRAPH_INDEX_CACHE[key]

    index = load_graph_index(in_path)
    _GRAPH_INDEX_CACHE[key] = index
    return index
