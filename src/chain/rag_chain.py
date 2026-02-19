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


def build_rag_chain(system_prompt: str | None = None):
    """Construct and return the full tutor RAG chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.
    """
    retriever = get_retriever()
    prompt = build_tutor_prompt(system_prompt=system_prompt)
    llm = _get_llm()

    # The chain:
    #   1. Run the retriever in parallel with passing the question through.
    #   2. Format retrieved docs into a context string.
    #   3. Feed context + question (+ optional chat history) into the prompt.
    #   4. Send prompt to the LLM.
    #   5. Parse the output to a plain string.
    extract_question = RunnableLambda(lambda x: x["question"])

    chain = (
        RunnableParallel(
            context=extract_question | retriever | _format_docs,
            question=extract_question,
            chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    logger.info("rag_chain_built", custom_system_prompt=bool(system_prompt))
    return chain
