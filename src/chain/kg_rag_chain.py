"""KG-RAG chain — wires the KG-expanded retriever with prompt and LLM using LCEL.

Same architecture as rag_chain.py but uses KG-guided retrieval instead of
plain similarity search.
"""

import structlog
from typing import Any, cast

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda

from src.chain.rag_chain import _format_docs
from src.kg.retriever import get_kg_retriever
from src.models import get_llm
from src.prompts import build_tutor_prompt
from src.prompts.templates import (
    format_conversation_summary,
    format_course_specific_instructions,
    resolve_system_prompt_mode,
)

from src.config import get_settings

logger = structlog.get_logger(__name__)


def _build_prompt_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Format retrieved documents for the tutor prompt while preserving raw docs."""
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
    """Return raw documents retrieved for this chain invocation."""
    return cast(list[Document], inputs["source_documents"])


def build_kg_rag_chain(
    chroma_collection: str | None = None,
    graph_scope: str | None = None,
):
    """Construct and return the KG-guided Socratic-tutor RAG chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields ``{"answer": str, "source_documents": list[Document]}``.

    chroma_collection: name of the ChromaDB collection to retrieve from.
        Defaults to the globally configured collection when None.
        Raises ValueError if the collection has not been ingested yet.
    """
    retriever = get_kg_retriever(
        collection_name=chroma_collection,
        graph_scope=graph_scope,
    )
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

    logger.info("kg_rag_chain_built")
    return chain
