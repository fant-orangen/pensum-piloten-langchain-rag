"""KG-RAG chain — wires the KG-expanded retriever with prompt and LLM using LCEL.

Same architecture as rag_chain.py but uses KG-guided retrieval instead of
plain similarity search.
"""

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnableLambda

from src.chain.rag_chain import _format_docs
from src.kg.retriever import get_kg_retriever
from src.models import get_llm
from src.prompts import build_tutor_prompt
from src.prompts.templates import resolve_system_prompt_mode

from src.config import get_settings

logger = structlog.get_logger(__name__)


def build_kg_rag_chain(chroma_collection: str | None = None):
    """Construct and return the KG-guided Socratic-tutor RAG chain.

    Returns an LCEL Runnable that accepts ``{"question": str, "chat_history": list}``
    and yields the tutor's response as a string.

    chroma_collection: name of the ChromaDB collection to retrieve from.
        Defaults to the globally configured collection when None.
        Raises ValueError if the collection has not been ingested yet.
    """
    retriever = get_kg_retriever(collection_name=chroma_collection)
    prompt = build_tutor_prompt()
    settings = get_settings()
    llm = get_llm(settings.temperature)

    extract_question = RunnableLambda(lambda x: x["question"])

    chain = (
        RunnableParallel(
            context=extract_question | retriever | _format_docs,
            question=extract_question,
            chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
            mode=RunnableLambda(
                lambda x: resolve_system_prompt_mode(x.get("system_prompt_mode"))
            ),
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    logger.info("kg_rag_chain_built")
    return chain
