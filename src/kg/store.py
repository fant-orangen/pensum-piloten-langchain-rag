"""Neo4j knowledge graph store — persists triplets as an entity graph.

Schema:
  (:Entity {name: str})
  (:Entity)-[:RELATED_TO {relation: str, chunk_id: str}]->(:Entity)

Chunks are not nodes. Each RELATED_TO edge carries the chunk_id of the chunk
it was extracted from, allowing retrieval to trace edges back to source text.
Multiple edges between the same entity pair are preserved (one per triplet),
enabling MST-based filtering at query time.
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

    def clear(self) -> None:
        """Remove all nodes and relationships from the graph."""
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("neo4j_cleared")

    def _create_indexes(self) -> None:
        with self._driver.session() as session:
            session.run(
                "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)"
            )

    def build_kg(self, triplets: list[Triplet]) -> None:
        """Populate the knowledge graph from extracted triplets.

        Each triplet becomes one RELATED_TO edge between two Entity nodes.
        Entity nodes are deduplicated by name via MERGE. Edges are created
        with CREATE so that multiple edges between the same entity pair
        (from different source chunks) are all preserved.
        """
        self.clear()
        self._create_indexes()

        with self._driver.session() as session:
            for t in triplets:
                session.run(
                    """
                    MERGE (h:Entity {name: $head})
                    MERGE (t:Entity {name: $tail})
                    WITH h, t
                    CREATE (h)-[:RELATED_TO {relation: $relation, chunk_id: $chunk_id}]->(t)
                    """,
                    head=t.head,
                    tail=t.tail,
                    relation=t.relation,
                    chunk_id=t.chunk_id,
                )

        with self._driver.session() as session:
            entity_count = session.run(
                "MATCH (e:Entity) RETURN count(e) AS cnt"
            ).single()["cnt"]
            edge_count = session.run(
                "MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS cnt"
            ).single()["cnt"]

        logger.info(
            "kg_built",
            entities=entity_count,
            edges=edge_count,
            triplets_ingested=len(triplets),
        )
