"""RAG chain assembly — wires retriever, prompt, and LLM together using LCEL.

The chain follows the standard Retrieval-Augmented Generation pattern:

    question  ──►  retriever  ──►  format context  ──►  prompt  ──►  LLM  ──►  answer

LangChain Expression Language (LCEL) is used so the chain is declarative,
streamable, and easy to extend (e.g. adding a reranker between retriever and
prompt is a one-line change).
"""

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

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

    def _format_page(raw_page: object) -> str:
        if raw_page == 0:
            return "0"
        if raw_page is None:
            return "-"
        page_str = str(raw_page).strip()
        return page_str if page_str else "-"

    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_file") or doc.metadata.get("source_path") or "unknown"
        page = _format_page(doc.metadata.get("page"))
        chunk_ref = doc.metadata.get("chunk_id")
        if not chunk_ref:
            chunk_index = doc.metadata.get("chunk_index")
            chunk_ref = f"c{chunk_index}" if chunk_index is not None else "-"

        header = f"[S{i}|{source}|p={page}|id={chunk_ref}]"
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


def _build_with_context_inputs():
    """Build reusable chain stage containing docs + formatted context."""
    retriever = get_retriever()
    extract_question = RunnableLambda(lambda x: x["question"])

    base_inputs = RunnableParallel(
        docs=extract_question | retriever,
        question=extract_question,
        chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
    )
    return base_inputs | RunnablePassthrough.assign(
        context=RunnableLambda(lambda x: _format_docs(x["docs"]))
    )


def _build_answer_runnable(system_prompt: str | None = None):
    """Build the prompt + llm answer branch that outputs plain text."""
    prompt = build_tutor_prompt(system_prompt=system_prompt)
    llm = _get_llm()
    return (
        RunnableLambda(
            lambda x: {
                "context": x["context"],
                "question": x["question"],
                "chat_history": x["chat_history"],
            }
        )
        | prompt
        | llm
        | StrOutputParser()
    )


def build_rag_chain(system_prompt: str | None = None):
    """Construct and return the tutor RAG chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.
    """
    with_context = _build_with_context_inputs()
    answer_branch = _build_answer_runnable(system_prompt=system_prompt)
    chain = with_context | answer_branch

    logger.info("rag_chain_built", custom_system_prompt=bool(system_prompt), with_sources=False)
    return chain


def build_rag_chain_with_sources(system_prompt: str | None = None):
    """Construct and return a RAG chain that outputs answer + retrieved docs.

    Output shape:
      {"answer": str, "docs": list[Document]}
    """
    with_context = _build_with_context_inputs()
    answer_branch = _build_answer_runnable(system_prompt=system_prompt)

    chain = (
        with_context
        | RunnablePassthrough.assign(answer=answer_branch)
        | RunnableLambda(lambda x: {"answer": x["answer"], "docs": x["docs"]})
    )

    logger.info("rag_chain_built", custom_system_prompt=bool(system_prompt), with_sources=True)
    return chain
