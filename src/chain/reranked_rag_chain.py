"""RAG chain using CrossEncoder reranked retrieval."""

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel

from src.chain.rag_chain import _format_docs
from src.models import get_llm
from src.prompts import build_tutor_prompt
from src.prompts.templates import (
    default_tutoring_instructions,
    format_conversation_summary,
    format_course_specific_instructions,
)
from src.retriever import get_reranked_retriever

logger = structlog.get_logger(__name__)


def build_reranked_rag_chain(
    chroma_collection: str | None = None,
    *,
    prompt_variant: str = "default",
):
    """Construct and return the CrossEncoder-reranked RAG chain."""
    retriever = get_reranked_retriever(collection_name=chroma_collection)
    prompt = build_tutor_prompt(template_variant=prompt_variant)
    llm = get_llm(temperature=0.3)

    extract_question = RunnableLambda(lambda x: x["question"])

    chain = (
        RunnableParallel(
            context=extract_question | retriever | _format_docs,
            question=extract_question,
            chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
            tutoring_instructions=RunnableLambda(
                lambda _: default_tutoring_instructions()
            ),
            course_specific_instructions=RunnableLambda(
                lambda x: format_course_specific_instructions(
                    x.get("course_specific_instructions")
                )
            ),
            conversation_summary=RunnableLambda(
                lambda x: format_conversation_summary(x.get("conversation_summary"))
            ),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    logger.info("reranked_rag_chain_built", collection=chroma_collection)
    return chain
