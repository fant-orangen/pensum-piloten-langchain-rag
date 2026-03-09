"""No-RAG chain assembly.

This baseline uses the same LLM and prompt style as the RAG chain but skips
retrieval entirely.
"""

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda

from src.models import get_llm
from src.prompts import build_tutor_prompt
from src.prompts.templates import (
    format_course_specific_instructions,
    resolve_system_prompt_mode,
)

logger = structlog.get_logger(__name__)


def build_no_rag_chain():
    """Construct and return the no-retrieval tutor chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.
    """
    prompt = build_tutor_prompt()
    llm = get_llm(temperature=0.3)

    extract_question = RunnableLambda(lambda x: x["question"])

    chain = (
        RunnableParallel(
            context=RunnableLambda(lambda _: ""),
            question=extract_question,
            chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
            mode=RunnableLambda(
                lambda x: resolve_system_prompt_mode(x.get("system_prompt_mode"))
            ),
            course_specific_instructions=RunnableLambda(
                lambda x: format_course_specific_instructions(
                    x.get("course_specific_instructions")
                )
            ),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    logger.info("no_rag_chain_built")
    return chain
