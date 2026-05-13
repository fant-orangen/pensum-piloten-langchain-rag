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
        """Close the underlying Neo4j driver."""

        self._driver.close()

    def clear(self, scope: str | None = None) -> None:
        """Remove all nodes and relationships from the graph or a single scope."""
        with self._driver.session() as session:
            if scope is None:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("neo4j_cleared")
                return
            session.run("MATCH (n:Entity {scope: $scope}) DETACH DELETE n", scope=scope)
        logger.info("neo4j_scope_cleared", scope=scope)

    def _create_indexes(self) -> None:
        """Create indexes needed for scoped entity lookup during ingestion/retrieval."""

        with self._driver.session() as session:
            session.run(
                "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.scope, e.name)"
            )

    def build_kg(self, triplets: list[Triplet], scope: str | None = None) -> None:
        """Populate the knowledge graph from extracted triplets.

        Each triplet becomes one RELATED_TO edge between two Entity nodes.
        Entity nodes are deduplicated by name via MERGE. Edges are created
        with CREATE so that multiple edges between the same entity pair
        (from different source chunks) are all preserved.
        """
        self.clear(scope=scope)
        self._create_indexes()

        with self._driver.session() as session:
            for t in triplets:
                if scope is None:
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
                    continue

                session.run(
                    """
                    MERGE (h:Entity {scope: $scope, name: $head})
                    MERGE (t:Entity {scope: $scope, name: $tail})
                    WITH h, t
                    CREATE (h)-[:RELATED_TO {
                        relation: $relation,
                        chunk_id: $chunk_id,
                        scope: $scope
                    }]->(t)
                    """,
                    scope=scope,
                    head=t.head,
                    tail=t.tail,
                    relation=t.relation,
                    chunk_id=t.chunk_id,
                )

        with self._driver.session() as session:
            if scope is None:
                entity_count = session.run(
                    "MATCH (e:Entity) RETURN count(e) AS cnt"
                ).single()["cnt"]
                edge_count = session.run(
                    "MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS cnt"
                ).single()["cnt"]
            else:
                entity_count = session.run(
                    "MATCH (e:Entity {scope: $scope}) RETURN count(e) AS cnt",
                    scope=scope,
                ).single()["cnt"]
                edge_count = session.run(
                    "MATCH (:Entity {scope: $scope})-[r:RELATED_TO {scope: $scope}]->(:Entity {scope: $scope}) RETURN count(r) AS cnt",
                    scope=scope,
                ).single()["cnt"]

        logger.info(
            "kg_built",
            entities=entity_count,
            edges=edge_count,
            triplets_ingested=len(triplets),
            scope=scope,
        )

    def get_expanded_subgraph(
        self,
        seed_chunk_ids: list[str],
        scope: str | None = None,
        hops: int | None = None,
    ) -> list[tuple[str, str, str, str]]:
        """Return all edges in the m-hop expanded subgraph of the seed chunks.

        Starting from all entities touched by edges whose chunk_id is in
        seed_chunk_ids, traverses up to `hops` hops along RELATED_TO edges
        and returns every edge in the resulting subgraph as
        (head, tail, relation, chunk_id).
        """
        settings = get_settings()
        hops = hops if hops is not None else settings.kg_expansion_hops

        if scope is None:
            query = f"""
                MATCH (h:Entity)-[r:RELATED_TO]->(t:Entity)
                WHERE r.chunk_id IN $seed_ids
                WITH COLLECT(DISTINCT h) + COLLECT(DISTINCT t) AS seed_entities
                UNWIND seed_entities AS se
                MATCH (se)-[:RELATED_TO*0..{int(hops)}]-(neighbor:Entity)
                WITH COLLECT(DISTINCT neighbor) AS all_entities
                UNWIND all_entities AS ae
                MATCH (ae)-[r2:RELATED_TO]->(other:Entity)
                WHERE other IN all_entities
                RETURN ae.name AS head, other.name AS tail,
                       r2.relation AS relation, r2.chunk_id AS chunk_id
            """
            params = {"seed_ids": seed_chunk_ids}
        else:
            query = f"""
                MATCH (h:Entity {{scope: $scope}})-[r:RELATED_TO {{scope: $scope}}]->(t:Entity {{scope: $scope}})
                WHERE r.chunk_id IN $seed_ids
                WITH COLLECT(DISTINCT h) + COLLECT(DISTINCT t) AS seed_entities
                UNWIND seed_entities AS se
                MATCH (se)-[:RELATED_TO*0..{int(hops)}]-(neighbor:Entity {{scope: $scope}})
                WITH COLLECT(DISTINCT neighbor) AS all_entities
                UNWIND all_entities AS ae
                MATCH (ae)-[r2:RELATED_TO {{scope: $scope}}]->(other:Entity {{scope: $scope}})
                WHERE other IN all_entities
                RETURN ae.name AS head, other.name AS tail,
                       r2.relation AS relation, r2.chunk_id AS chunk_id
            """
            params = {"seed_ids": seed_chunk_ids, "scope": scope}

        with self._driver.session() as session:
            result = session.run(query, **params)
            edges = [
                (rec["head"], rec["tail"], rec["relation"], rec["chunk_id"])
                for rec in result
            ]

        logger.info(
            "kg_subgraph_fetched",
            seed_count=len(seed_chunk_ids),
            edge_count=len(edges),
            scope=scope,
        )
        return edges
