from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field


class CrossEncoderRerankRetriever(BaseRetriever):
    base_retriever: BaseRetriever = Field(...)
    cross_encoder: object = Field(...)
    top_k: int = Field(default=5)

    def _rerank(self, query: str, docs: List[Document]) -> List[Document]:
        if not docs:
            return docs

        pairs = [(query, d.page_content) for d in docs]
        scores = self.cross_encoder.predict(pairs)

        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [d for d, _ in ranked[: self.top_k]]

    def _get_relevant_documents(self, query: str) -> List[Document]:
        docs = self.base_retriever.get_relevant_documents(query)
        return self._rerank(query, docs)

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        docs = await self.base_retriever.aget_relevant_documents(query)
        return self._rerank(query, docs)