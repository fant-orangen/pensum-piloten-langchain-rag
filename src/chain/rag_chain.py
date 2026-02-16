"""RAG chain assembly — wires retriever, prompt, and LLM together using LCEL.

The chain follows the standard Retrieval-Augmented Generation pattern:

    question  ──►  retriever  ──►  format context  ──►  prompt  ──►  LLM  ──►  answer

LangChain Expression Language (LCEL) is used so the chain is declarative,
streamable, and easy to extend (e.g. adding a reranker between retriever and
prompt is a one-line change).
"""

import re

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda, RunnablePassthrough
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from src.config import get_settings
from src.retriever import get_retriever
from src.prompts import build_tutor_prompt, normalise_teaching_mode

logger = structlog.get_logger(__name__)

_GROUNDING_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]{2,}")
_GROUNDING_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "between",
    "could",
    "does",
    "from",
    "have",
    "into",
    "just",
    "many",
    "more",
    "most",
    "other",
    "some",
    "than",
    "that",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "very",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "your",
}


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


def _token_set(text: str) -> set[str]:
    return {
        token.lower()
        for token in _GROUNDING_TOKEN_RE.findall(text)
        if token.lower() not in _GROUNDING_STOPWORDS
    }


def _should_keep_segment(segment: str, context_tokens: set[str], min_overlap: float) -> bool:
    stripped = segment.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", "-", "*")):
        return True
    if stripped.endswith("?"):
        return True

    seg_tokens = _token_set(stripped)
    if len(seg_tokens) < 4:
        return True

    overlap = len(seg_tokens.intersection(context_tokens)) / float(len(seg_tokens))
    return overlap >= min_overlap


def _apply_grounding(payload: dict[str, str]) -> str:
    settings = get_settings()
    answer = payload["answer"]
    if not settings.grounding_enabled:
        return answer

    context = payload["context"]
    context_tokens = _token_set(context)
    segments = [segment.strip() for segment in re.split(r"(?<=[.!?])\s+|\n+", answer) if segment.strip()]
    if not segments:
        return answer

    kept: list[str] = []
    removed = 0
    for segment in segments:
        if _should_keep_segment(segment, context_tokens, settings.grounding_min_overlap):
            kept.append(segment)
        else:
            removed += 1

    if removed == 0:
        return answer

    logger.info(
        "grounding_check",
        removed_segments=removed,
        total_segments=len(segments),
        mode=settings.grounding_mode,
    )

    if settings.grounding_mode == "prune":
        pruned = " ".join(kept).strip()
        if not pruned:
            return (
                "I could not confidently ground the answer in the retrieved material. "
                "Please ask a more specific question or provide more context."
            )
        return pruned

    note = (
        "\n\nNote: Some details may not be fully supported by the retrieved material. "
        "Verify against the cited sources."
    )
    return answer + note


def build_rag_chain(teaching_mode: str | None = None):
    """Construct and return the full RAG chain with selected teaching mode.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.
    """
    selected_mode = normalise_teaching_mode(teaching_mode)
    retriever = get_retriever()
    prompt = build_tutor_prompt(selected_mode)
    llm = _get_llm()

    # The chain:
    #   1. Run the retriever in parallel with passing the question through.
    #   2. Format retrieved docs into a context string.
    #   3. Feed context + question (+ optional chat history) into the prompt.
    #   4. Send prompt to the LLM.
    #   5. Parse the output to a plain string.
    extract_question = RunnableLambda(lambda x: x["question"])

    prepared_inputs = RunnableParallel(
        context=extract_question | retriever | _format_docs,
        question=extract_question,
        chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
    )

    chain = (
        prepared_inputs
        | RunnablePassthrough.assign(answer=prompt | llm | StrOutputParser())
        | RunnableLambda(
            lambda x: _apply_grounding(
                {
                    "answer": x["answer"],
                    "context": x["context"],
                    "question": x["question"],
                }
            )
        )
    )

    logger.info("rag_chain_built", teaching_mode=selected_mode)
    return chain
