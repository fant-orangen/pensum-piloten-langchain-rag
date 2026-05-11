"""Naive RAG chain using only vector similarity retrieval."""

from typing import Any, cast

import structlog
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel

from src.chain.rag_chain import _format_docs
from src.config import get_settings
from src.models import get_llm
from src.naive.retriever import get_naive_retriever
from src.prompts import build_tutor_prompt
from src.prompts.templates import (
    format_conversation_summary,
    format_course_specific_instructions,
    resolve_system_prompt_mode,
)

logger = structlog.get_logger(__name__)


def _build_prompt_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Format retrieved chunks for the tutor prompt while preserving sources."""
    source_documents = cast(list[Document], inputs["source_documents"])
    return {
        "context": _format_docs(source_documents),
        "question": inputs["question"],
        "chat_history": inputs.get("chat_history", []),
        "mode": inputs["mode"],
        "course_specific_instructions": inputs["course_specific_instructions"],
        "conversation_summary": inputs["conversation_summary"],
    }


def _extract_source_documents(inputs: dict[str, Any]) -> list[Document]:
    """Return raw vector-retrieved documents for persistence."""
    return cast(list[Document], inputs["source_documents"])


def build_naive_rag_chain(chroma_collection: str | None = None):
    """Build a course-scoped vector-only RAG chain.

    The returned runnable matches the KG-RAG output shape:
    ``{"answer": str, "source_documents": list[Document]}``.
    """
    retriever = get_naive_retriever(collection_name=chroma_collection)
    prompt = build_tutor_prompt()
    settings = get_settings()
    llm = get_llm(settings.temperature)

    extract_question = RunnableLambda(lambda x: x["question"])
    retrieval_inputs = RunnableParallel(
        source_documents=extract_question | retriever,
        question=extract_question,
        chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
        mode=RunnableLambda(lambda x: resolve_system_prompt_mode(x.get("system_prompt_mode"))),
        course_specific_instructions=RunnableLambda(
            lambda x: format_course_specific_instructions(x.get("course_specific_instructions"))
        ),
        conversation_summary=RunnableLambda(
            lambda x: format_conversation_summary(x.get("conversation_summary"))
        ),
    )

    answer_chain = RunnableLambda(_build_prompt_inputs) | prompt | llm | StrOutputParser()
    chain = retrieval_inputs | RunnableParallel(
        answer=answer_chain,
        source_documents=RunnableLambda(_extract_source_documents),
    )
    logger.info("naive_rag_chain_built", collection=chroma_collection)
    return chain
