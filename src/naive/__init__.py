"""Naive vector-only RAG components."""

from src.naive.chain import build_naive_rag_chain
from src.naive.retriever import get_naive_retriever

__all__ = ["build_naive_rag_chain", "get_naive_retriever"]
