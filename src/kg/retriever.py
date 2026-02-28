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

    @staticmethod
    def _seed_documents(seed_pairs: list[tuple[Document, float]]) -> list[Document]:
        """Strip similarity scores from seed pairs.

        Args:
            seed_pairs: Tuples from vector search in the form ``(Document, distance)``.

        Returns:
            The documents only, preserving original search order.
        """
        return [doc for doc, _ in seed_pairs]

    def _retrieve_seed_pairs(self, query: str) -> list[tuple[Document, float]]:
        """Run semantic retrieval to obtain top-k seed chunks.

        Uses Chroma similarity search and returns distance scores (L2),
        where lower values indicate higher semantic similarity.

        Args:
            query: User query to embed and retrieve against.

        Returns:
            Ordered list of ``(Document, distance)`` tuples.
        """
        vectorstore = get_vectorstore()
        seed_pairs = vectorstore.similarity_search_with_score(query, k=self.top_k)
        logger.info("seed_retrieval", count=len(seed_pairs))
        return seed_pairs

    @staticmethod
    def _extract_seed_ids(seed_pairs: list[tuple[Document, float]]) -> list[str]:
        """Extract ``chunk_id`` values from retrieved seed documents.

        Args:
            seed_pairs: Tuples returned from seed retrieval.

        Returns:
            List of chunk IDs for documents that include ``chunk_id`` metadata.
        """
        return [
            doc.metadata["chunk_id"]
            for doc, _ in seed_pairs
            if "chunk_id" in doc.metadata
        ]

    def _fetch_subgraph_edges(self, seed_ids: list[str]) -> list[tuple[str, str, str, str]]:
        """Fetch expanded KG edges around seed chunks.

        Args:
            seed_ids: Chunk IDs that anchor graph expansion.

        Returns:
            List of raw edge tuples ``(head, tail, relation, chunk_id)``.
        """
        return self.kg_store.get_expanded_subgraph(seed_ids)

    @staticmethod
    def _build_seed_scores(seed_pairs: list[tuple[Document, float]]) -> dict[str, float]:
        """Convert seed L2 distances to normalized similarity scores.

        Distances are mapped by ``similarity = 1 / (1 + distance)`` to produce
        scores in the range ``(0, 1]``.

        Args:
            seed_pairs: Tuples of ``(Document, distance)``.

        Returns:
            Mapping from ``chunk_id`` to normalized similarity score.
        """
        return {
            doc.metadata["chunk_id"]: 1.0 / (1.0 + score)
            for doc, score in seed_pairs
            if "chunk_id" in doc.metadata
        }

    @staticmethod
    def _find_unscored_ids(
        raw_edges: list[tuple[str, str, str, str]], scores: dict[str, float]
    ) -> list[str]:
        """Find chunk IDs in the subgraph that still lack similarity scores.

        Args:
            raw_edges: Expanded subgraph edges.
            scores: Existing score map, typically initialized from seed chunks.

        Returns:
            Chunk IDs present on edges but missing from ``scores``.
        """
        all_edge_chunk_ids = {chunk_id for _, _, _, chunk_id in raw_edges}
        return [cid for cid in all_edge_chunk_ids if cid not in scores]

    @staticmethod
    def _score_unscored_chunk_ids(
        query: str,
        vectorstore: Any,
        unscored_ids: list[str],
        scores: dict[str, float],
    ) -> None:
        """Score non-seed subgraph chunks using a batched vector query.

        This mutates ``scores`` in place by adding entries for any IDs found
        in Chroma. Distances are converted to similarities with
        ``1 / (1 + distance)`` for consistency with seed scoring.

        Args:
            query: Original user query.
            vectorstore: Vector store instance used for direct collection access.
            unscored_ids: Chunk IDs needing scores.
            scores: Mutable mapping of ``chunk_id -> similarity``.

        Returns:
            ``None``. The ``scores`` dictionary is updated in place.
        """
        if not unscored_ids:
            return

        collection = vectorstore._collection
        query_embedding = vectorstore._embedding_function.embed_query(query)
        scored = collection.query(
            query_embeddings=[query_embedding],
            where={"chunk_id": {"$in": unscored_ids}},
            n_results=min(len(unscored_ids), collection.count()),
            include=["metadatas", "distances"],
        )
        if not (scored and scored["metadatas"]):
            return

        for meta, dist in zip(scored["metadatas"][0], scored["distances"][0]):
            cid = meta.get("chunk_id")
            if cid:
                scores[cid] = 1.0 / (1.0 + dist)

    @staticmethod
    def _build_weighted_edges(
        raw_edges: list[tuple[str, str, str, str]], scores: dict[str, float]
    ) -> list[WeightedEdge]:
        """Attach chunk relevance scores to graph edges.

        Args:
            raw_edges: Raw KG edges as ``(head, tail, relation, chunk_id)`` tuples.
            scores: Similarity scores keyed by ``chunk_id``.

        Returns:
            Weighted edges used by MST filtering. Edges whose chunk IDs are
            not present in ``scores`` are skipped.
        """
        return [
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

    @staticmethod
    def _collect_ordered_chunk_ids(components: list[list[WeightedEdge]]) -> list[str]:
        """Collect deduplicated chunk IDs in component order.

        Component order is preserved from ``build_mst_subgraphs`` output, and
        each chunk ID appears only once in first-seen order.

        Args:
            components: MST edges grouped by connected component.

        Returns:
            Ordered, deduplicated chunk ID list.
        """
        seen: set[str] = set()
        ordered_ids: list[str] = []
        for component in components:
            for edge in component:
                if edge.chunk_id not in seen:
                    seen.add(edge.chunk_id)
                    ordered_ids.append(edge.chunk_id)
        return ordered_ids

    @staticmethod
    def _apply_score_threshold(ordered_ids: list[str], scores: dict[str, float]) -> list[str]:
        """Limit final chunk IDs by similarity to a configured maximum count.

        Args:
            ordered_ids: Candidate chunk IDs in relevance order.
            scores: Similarity score map by ``chunk_id``.

        Returns:
            At most ``kg_max_final_chunks`` IDs, where lowest-similarity IDs are
            removed first. Relative order among retained IDs is preserved.
        """
        max_chunks = get_settings().kg_max_final_chunks
        if len(ordered_ids) <= max_chunks:
            return ordered_ids

        top_ids = sorted(
            ordered_ids,
            key=lambda cid: scores.get(cid, 0.0),
            reverse=True,
        )[:max_chunks]
        keep_ids = set(top_ids)
        return [cid for cid in ordered_ids if cid in keep_ids]

    @staticmethod
    def _append_missing_seed_ids(ordered_ids: list[str], seed_ids: list[str]) -> list[str]:
        """Ensure all seed chunk IDs are included in final retrieval order.

        Missing seeds are appended to the end while preserving existing order.

        Args:
            ordered_ids: Current ordered chunk IDs.
            seed_ids: Seed IDs from semantic retrieval.

        Returns:
            Updated ordered IDs containing all seeds at least once.
        """
        seen = set(ordered_ids)
        for cid in seed_ids:
            if cid not in seen:
                seen.add(cid)
                ordered_ids.append(cid)
        return ordered_ids

    @staticmethod
    def _fetch_docs_by_chunk_id(vectorstore: Any, ordered_ids: list[str]) -> list[Document]:
        """Fetch documents by chunk IDs and return them in requested order.

        Args:
            vectorstore: Vector store instance exposing the underlying collection.
            ordered_ids: Chunk IDs in desired output order.

        Returns:
            List of LangChain ``Document`` objects matching ``ordered_ids`` order.
            Missing IDs are silently ignored.
        """
        collection = vectorstore._collection
        results = collection.get(
            where={"chunk_id": {"$in": ordered_ids}},
            include=["documents", "metadatas"],
        )

        id_to_doc: dict[str, Document] = {}
        if results and results["documents"]:
            for doc_text, meta in zip(results["documents"], results["metadatas"]):
                cid = meta.get("chunk_id")
                if cid:
                    id_to_doc[cid] = Document(page_content=doc_text, metadata=meta)

        return [id_to_doc[cid] for cid in ordered_ids if cid in id_to_doc]

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        """Retrieve query-relevant documents using the KG2RAG-style pipeline.

        High-level flow:
          1. Retrieve semantic seed chunks from Chroma.
          2. Expand through the KG around seed chunks.
          3. Score all edge-referenced chunks.
          4. Build weighted edges and run MST filtering per component.
          5. Collect ordered chunk IDs, threshold low-similarity chunks.
          6. Ensure seed chunks are retained and fetch final documents.

        Args:
            query: User query string.
            run_manager: LangChain callback manager (required by retriever API).

        Returns:
            Ordered list of retrieved documents. Falls back to seed documents
            if graph expansion or MST filtering yields no usable chunk IDs.
        """
        vectorstore = get_vectorstore()
        seed_pairs = self._retrieve_seed_pairs(query)
        seed_ids = self._extract_seed_ids(seed_pairs)
        if not seed_ids:
            logger.warning("no_chunk_ids_in_seeds")
            return self._seed_documents(seed_pairs)

        raw_edges = self._fetch_subgraph_edges(seed_ids)
        if not raw_edges:
            logger.warning("empty_subgraph", seed_ids=seed_ids)
            return self._seed_documents(seed_pairs)

        scores = self._build_seed_scores(seed_pairs)
        unscored_ids = self._find_unscored_ids(raw_edges, scores)
        self._score_unscored_chunk_ids(query, vectorstore, unscored_ids, scores)

        weighted_edges = self._build_weighted_edges(raw_edges, scores)
        components = build_mst_subgraphs(weighted_edges)

        ordered_ids = self._collect_ordered_chunk_ids(components)
        if not ordered_ids:
            return self._seed_documents(seed_pairs)

        ordered_ids = self._apply_score_threshold(ordered_ids, scores)
        if not ordered_ids:
            return self._seed_documents(seed_pairs)

        ordered_ids = self._append_missing_seed_ids(ordered_ids, seed_ids)
        final_docs = self._fetch_docs_by_chunk_id(vectorstore, ordered_ids)

        logger.info(
            "kg_mst_retrieval",
            seeds=len(seed_ids),
            subgraph_edges=len(raw_edges),
            components=len(components),
            final_chunks=len(final_docs),
        )
        return final_docs


def get_kg_retriever() -> KGExpandedRetriever:
    """Construct a configured ``KGExpandedRetriever`` instance.

    Returns:
        Retriever configured with project settings and a fresh ``KGStore``.
    """
    settings = get_settings()
    kg_store = KGStore()
    return KGExpandedRetriever(kg_store=kg_store, top_k=settings.retriever_top_k)
