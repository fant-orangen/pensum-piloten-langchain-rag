"""KG-expanded retriever — combines semantic search with knowledge graph traversal.

Pipeline:
  1. Semantic similarity search (ChromaDB) -> seed chunks
  2. Extract chunk IDs from seed results
  3. Expand via KG traversal (Neo4j) -> additional chunk IDs
  4. Fetch expanded chunks from ChromaDB
  5. Return merged, deduplicated results
"""

from typing import Any

import structlog
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from src.config import get_settings
from src.kg.store import KGStore
from src.vectorstore.store import get_vectorstore

logger = structlog.get_logger(__name__)


class KGExpandedRetriever(BaseRetriever):
    """A retriever that uses KG graph traversal to expand semantic search results."""

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

        # Step 1: Semantic similarity search for seed chunks
        seed_results = vectorstore.similarity_search(query, k=self.top_k)
        logger.info("seed_retrieval", count=len(seed_results))

        # Step 2: Get chunk IDs from seed results
        seed_ids = [
            doc.metadata["chunk_id"]
            for doc in seed_results
            if "chunk_id" in doc.metadata
        ]

        if not seed_ids:
            logger.warning("no_chunk_ids_in_seeds")
            return seed_results

        # Step 3: Expand via KG
        expanded_ids = self.kg_store.get_expanded_chunk_ids(seed_ids)

        # Step 4: Fetch expanded chunks from ChromaDB (excluding already-retrieved seeds)
        new_ids = [cid for cid in expanded_ids if cid not in set(seed_ids)]

        expanded_docs: list[Document] = []
        if new_ids:
            collection = vectorstore._collection
            results = collection.get(
                where={"chunk_id": {"$in": new_ids}},
                include=["documents", "metadatas"],
            )
            if results and results["documents"]:
                for doc_text, meta in zip(results["documents"], results["metadatas"]):
                    expanded_docs.append(Document(page_content=doc_text, metadata=meta))

        logger.info(
            "kg_expanded_retrieval",
            seed=len(seed_results),
            expanded=len(expanded_docs),
            total=len(seed_results) + len(expanded_docs),
        )

        # Merge: seeds first, then expanded
        return seed_results + expanded_docs


def get_kg_retriever() -> KGExpandedRetriever:
    """Build and return a KG-expanded retriever."""
    settings = get_settings()
    kg_store = KGStore()
    return KGExpandedRetriever(kg_store=kg_store, top_k=settings.retriever_top_k)
