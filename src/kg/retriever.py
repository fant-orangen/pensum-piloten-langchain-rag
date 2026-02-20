"""KG-RAG retriever — semantic search + graph expansion + MST filtering.

Pipeline (per the KG2RAG paper):
  1. Semantic similarity search (ChromaDB) -> seed chunks with scores
  2. Expand via KG traversal (Neo4j) -> subgraph edges (head, tail, relation, chunk_id)
  3. Score all chunks referenced by subgraph edges via embedding similarity
  4. Attach scores to edges as weights -> WeightedEdge list
  5. MST filtering (organizer) -> one MST per connected component
  6. Read surviving chunk_ids from MST edges, fetch from ChromaDB
  7. Return chunks in component-relevance order
"""

from typing import Any

import structlog
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from src.config import get_settings
from src.kg.organizer import WeightedEdge, build_mst_subgraphs
from src.kg.store import KGStore
from src.vectorstore.store import get_vectorstore

logger = structlog.get_logger(__name__)


class KGExpandedRetriever(BaseRetriever):
    """Retriever that combines KG-guided expansion with MST-based context filtering."""

    kg_store: Any = None
    top_k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        vectorstore = get_vectorstore()

        # Step 1: Semantic search — seeds with similarity scores.
        # Scores are needed as edge weights; similarity_search_with_score returns
        # (Document, float) pairs where float is an L2 distance (lower = more similar).
        seed_pairs = vectorstore.similarity_search_with_score(query, k=self.top_k)
        logger.info("seed_retrieval", count=len(seed_pairs))

        seed_ids = [
            doc.metadata["chunk_id"]
            for doc, _ in seed_pairs
            if "chunk_id" in doc.metadata
        ]
        if not seed_ids:
            logger.warning("no_chunk_ids_in_seeds")
            return [doc for doc, _ in seed_pairs]

        # Step 2: Fetch the full expanded subgraph edges from Neo4j.
        # Returns (head, tail, relation, chunk_id) for every edge in the
        # m-hop neighbourhood of seed entities.
        raw_edges = self.kg_store.get_expanded_subgraph(seed_ids)
        if not raw_edges:
            logger.warning("empty_subgraph", seed_ids=seed_ids)
            return [doc for doc, _ in seed_pairs]

        # Step 3: Preprocessing for seed chunks.
        # Seed scores come from Step 1. Convert L2 distance to similarity in (0,1]
        # so that all weights are on the same scale as expanded chunk scores below.
        scores: dict[str, float] = {
            doc.metadata["chunk_id"]: 1.0 / (1.0 + score)
            for doc, score in seed_pairs
            if "chunk_id" in doc.metadata
        }
        all_edge_chunk_ids = {chunk_id for _, _, _, chunk_id in raw_edges}
        unscored_ids = [cid for cid in all_edge_chunk_ids if cid not in scores] # unscored ids = chunk ids in the expanded subgraph that are not in the seed chunks

        # 
        # Step 3b: Score unscored chunk_ids in the expanded subgraph.
        # For all chunk_ids found in the expanded subgraph that do not have
        # a similarity score from the original semantic search (i.e., were not
        # in the top-k seed chunks), perform a batched similarity search to assign
        # them a score. This ensures every chunk_id in the subgraph is assigned
        # a relevance score for the subsequent MST filtering step.
        # The scoring is done by querying the vectorstore for embeddings whose
        # chunk_id is in unscored_ids, returning L2 distances which are then
        # converted to similarity scores in (0,1] by 1/(1+dist).
        if unscored_ids:
            collection = vectorstore._collection
            query_embedding = vectorstore._embedding_function.embed_query(query)
            scored = collection.query(
                query_embeddings=[query_embedding],
                where={"chunk_id": {"$in": unscored_ids}},
                n_results=min(len(unscored_ids), collection.count()),
                include=["metadatas", "distances"],
            )
            if scored and scored["metadatas"]:
                for meta, dist in zip(scored["metadatas"][0], scored["distances"][0]):
                    cid = meta.get("chunk_id")
                    if cid:
                        # Chroma distances are L2; convert to similarity in [0,1]
                        scores[cid] = 1.0 / (1.0 + dist)

        # Step 4: Construct WeightedEdge list — attach scores to edges.
        # Edges whose chunk_id has no score (chunk absent from Chroma) are skipped.
        weighted_edges = [
            WeightedEdge(
                head=head,
                tail=tail,
                relation=relation,
                chunk_id=chunk_id,
                weight=scores[chunk_id],
            )
            for head, tail, relation, chunk_id in raw_edges
            if chunk_id in scores
        ]

        # Step 5: MST filtering — one maximum spanning tree per connected component.
        # Returns components sorted by mean edge weight descending.
        components = build_mst_subgraphs(weighted_edges)

        # Step 6: Collect chunk_ids from MST edges in component order, deduplicated.
        # Deduplication is needed because one chunk can contribute edges in one component.
        seen: set[str] = set()
        ordered_ids: list[str] = []
        for component in components:
            for edge in component:
                if edge.chunk_id not in seen:
                    seen.add(edge.chunk_id)
                    ordered_ids.append(edge.chunk_id)

        if not ordered_ids:
            return [doc for doc, _ in seed_pairs]

        # Filter out chunks below the minimum similarity threshold.
        min_score = get_settings().kg_min_chunk_score
        ordered_ids = [cid for cid in ordered_ids if scores.get(cid, 0.0) >= min_score]

        if not ordered_ids:
            return [doc for doc, _ in seed_pairs]

        # Step 7: Fetch the final chunk set from ChromaDB.
        collection = vectorstore._collection
        results = collection.get(
            where={"chunk_id": {"$in": ordered_ids}},
            include=["documents", "metadatas"],
        )

        id_to_doc: dict[str, Document] = {}
        if results and results["documents"]:
            for doc_text, meta in zip(results["documents"], results["metadatas"]):
                cid = meta.get("chunk_id")
                if cid in seen:
                    id_to_doc[cid] = Document(page_content=doc_text, metadata=meta)

        # Return in MST component order (most relevant component first).
        final_docs = [id_to_doc[cid] for cid in ordered_ids if cid in id_to_doc]

        logger.info(
            "kg_mst_retrieval",
            seeds=len(seed_ids),
            subgraph_edges=len(raw_edges),
            components=len(components),
            final_chunks=len(final_docs),
        )
        return final_docs


def get_kg_retriever() -> KGExpandedRetriever:
    """Build and return a KG-expanded retriever."""
    settings = get_settings()
    kg_store = KGStore()
    return KGExpandedRetriever(kg_store=kg_store, top_k=settings.retriever_top_k)
