"""Neo4j knowledge graph store — persists triplets and supports graph-guided expansion.

Schema:
  (:Entity {name, normalized_name})
  (:Chunk  {chunk_id, source_file, page})
  (:Entity)-[:RELATED_TO {relation}]->(:Entity)
  (:Chunk)-[:MENTIONS]->(:Entity)
"""

import structlog
from neo4j import GraphDatabase

from src.config import get_settings
from src.kg.extractor import Triplet

logger = structlog.get_logger(__name__)


class KGStore:
    """Wrapper around a Neo4j driver for knowledge graph operations."""

    def __init__(self) -> None:
        settings = get_settings()
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        logger.info("neo4j_connected", uri=settings.neo4j_uri)

    def close(self) -> None:
        self._driver.close()

    def _create_indexes(self) -> None:
        """Create indexes for efficient lookups."""
        with self._driver.session() as session:
            session.run(
                "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.normalized_name)"
            )
            session.run(
                "CREATE INDEX IF NOT EXISTS FOR (c:Chunk) ON (c.chunk_id)"
            )

    def clear(self) -> None:
        """Remove all nodes and relationships from the graph."""
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("neo4j_cleared")

    def build_kg(
        self,
        triplets: list[Triplet],
        chunk_metadata: dict[str, dict],
    ) -> None:
        """Populate the knowledge graph from extracted triplets.

        Args:
            triplets: Extracted (head, relation, tail, chunk_id) tuples.
            chunk_metadata: Mapping of chunk_id -> {source_file, page} for Chunk nodes.
        """
        self.clear()
        self._create_indexes()

        with self._driver.session() as session:
            # Create Chunk nodes
            for chunk_id, meta in chunk_metadata.items():
                session.run(
                    """
                    MERGE (c:Chunk {chunk_id: $chunk_id})
                    SET c.source_file = $source_file, c.page = $page
                    """,
                    chunk_id=chunk_id,
                    source_file=meta.get("source_file", "unknown"),
                    page=str(meta.get("page", "")),
                )

            # Create Entity nodes, RELATED_TO edges, and MENTIONS edges
            for t in triplets:
                session.run(
                    """
                    MERGE (h:Entity {normalized_name: $head})
                    ON CREATE SET h.name = $head
                    MERGE (t:Entity {normalized_name: $tail})
                    ON CREATE SET t.name = $tail
                    MERGE (h)-[:RELATED_TO {relation: $relation}]->(t)
                    WITH h, t
                    MATCH (c:Chunk {chunk_id: $chunk_id})
                    MERGE (c)-[:MENTIONS]->(h)
                    MERGE (c)-[:MENTIONS]->(t)
                    """,
                    head=t.head,
                    tail=t.tail,
                    relation=t.relation,
                    chunk_id=t.chunk_id,
                )

        with self._driver.session() as session:
            result = session.run(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt"
            )
            for record in result:
                logger.info("kg_node_count", label=record["label"], count=record["cnt"])

    def get_expanded_chunk_ids(
        self,
        seed_chunk_ids: list[str],
        hops: int | None = None,
        max_chunks: int | None = None,
    ) -> list[str]:
        """Given seed chunk IDs, traverse the KG to find related chunks.

        1. Find entities mentioned by seed chunks.
        2. Traverse up to `hops` hops along RELATED_TO edges.
        3. Find all chunks that mention those neighbor entities.
        4. Return deduplicated chunk IDs (including seeds).
        """
        settings = get_settings()
        hops = hops or settings.kg_expansion_hops
        max_chunks = max_chunks or settings.kg_max_expanded_chunks

        # Neo4j does not support parameters in variable-length patterns,
        # so we interpolate the hops value (always an int, safe from injection).
        query = f"""
            MATCH (seed:Chunk)-[:MENTIONS]->(e:Entity)
            WHERE seed.chunk_id IN $seed_ids
            WITH COLLECT(DISTINCT e) AS seed_entities
            UNWIND seed_entities AS se
            MATCH (se)-[:RELATED_TO*0..{int(hops)}]-(neighbor:Entity)
            WITH COLLECT(DISTINCT neighbor) AS all_entities
            UNWIND all_entities AS ae
            MATCH (expanded:Chunk)-[:MENTIONS]->(ae)
            RETURN DISTINCT expanded.chunk_id AS chunk_id
            LIMIT $max_chunks
        """

        with self._driver.session() as session:
            result = session.run(
                query,
                seed_ids=seed_chunk_ids,
                max_chunks=max_chunks,
            )
            expanded_ids = [record["chunk_id"] for record in result]

        logger.info(
            "kg_expansion",
            seed_count=len(seed_chunk_ids),
            expanded_count=len(expanded_ids),
        )
        return expanded_ids
