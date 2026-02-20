"""RAG chain assembly — wires retriever, prompt, and LLM together using LCEL.

The chain follows the standard Retrieval-Augmented Generation pattern:

    question  ──►  retriever  ──►  format context  ──►  prompt  ──►  LLM  ──►  answer

LangChain Expression Language (LCEL) is used so the chain is declarative,
streamable, and easy to extend (e.g. adding a reranker between retriever and
prompt is a one-line change).
"""

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from typing import Any

from src.config import get_settings
from src.retriever import get_retriever
from src.prompts import build_tutor_prompt

logger = structlog.get_logger(__name__)


def _format_docs(docs: list[Document]) -> str:
    """Concatenate retrieved documents into a single context string.

    Each chunk is separated by a visual divider and prefixed with its source
    metadata so the LLM can cite it.
    """
    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_file", "unknown")
        page = doc.metadata.get("page", "")
        header = f"[Source {i}: {source}"
        if page:
            header += f", p. {page}"
        header += "]"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _get_llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.llm_model_name,
        openai_api_key=settings.openai_api_key,
        temperature=0.3,       # low temp for factual grounding
        streaming=True,
    )


def _extract_question(payload: dict[str, Any]) -> str:
    question = payload.get("question", "")
    return str(question)


def _extract_chat_history(payload: dict[str, Any]) -> list[Any]:
    history = payload.get("chat_history", [])
    return history if isinstance(history, list) else []


def _extract_docs(payload: dict[str, Any]) -> list[Document]:
    docs = payload.get("docs")
    if not isinstance(docs, list):
        return []
    return [doc for doc in docs if isinstance(doc, Document)]


def _to_prompt_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    docs = _extract_docs(payload)
    return {
        "context": _format_docs(docs),
        "question": _extract_question(payload),
        "chat_history": _extract_chat_history(payload),
    }


def _build_retrieval_payload():
    retriever = get_retriever()
    return RunnableParallel(
        docs=RunnableLambda(_extract_question) | retriever,
        question=RunnableLambda(_extract_question),
        chat_history=RunnableLambda(_extract_chat_history),
    )


def build_rag_chain(system_prompt: str | None = None):
    """Construct and return the full Socratic-tutor RAG chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.
    """
    prompt = build_tutor_prompt(system_prompt=system_prompt)
    llm = _get_llm()
    chain = (
        _build_retrieval_payload()
        | RunnableLambda(_to_prompt_inputs)
        | prompt
        | llm
        | StrOutputParser()
    )

    logger.info("rag_chain_built")
    return chain


def build_rag_chain_with_sources(system_prompt: str | None = None):
    """Construct and return a RAG chain that includes retrieved documents.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields ``{"answer": str, "docs": list[Document]}``.
    """
    prompt = build_tutor_prompt(system_prompt=system_prompt)
    llm = _get_llm()
    answer_chain = RunnableLambda(_to_prompt_inputs) | prompt | llm | StrOutputParser()

    chain = (
        _build_retrieval_payload()
        | RunnableParallel(
            answer=answer_chain,
            docs=RunnableLambda(_extract_docs),
        )
    )

    logger.info("rag_chain_with_sources_built")
    return chain
