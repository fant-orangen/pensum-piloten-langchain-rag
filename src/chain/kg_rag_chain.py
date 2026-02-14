"""KG-RAG chain — wires the KG-expanded retriever with prompt and LLM using LCEL.

Same architecture as rag_chain.py but uses KG-guided retrieval instead of
plain similarity search.
"""

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda

from src.chain.rag_chain import _format_docs, _get_llm
from src.kg.retriever import get_kg_retriever
from src.prompts import build_tutor_prompt

logger = structlog.get_logger(__name__)


def build_kg_rag_chain():
    """Construct and return the KG-guided Socratic-tutor RAG chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.
    """
    retriever = get_kg_retriever()
    prompt = build_tutor_prompt()
    llm = _get_llm()

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

    logger.info("kg_rag_chain_built")
    return chain
