"""Automated KG-RAG chat test between tutor AI and tester AI.

Usage:
    python -m scripts.generate_test
"""

import json
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel

from src.chain.kg_rag_chain import build_kg_rag_chain
from src.config import Settings, get_settings
from src.models import get_llm
from src.prompts.templates import build_tester_prompt

_LOG_DIR = Path("data/test_logs")

def _build_tester_chain():
    """Return the tester chain that generates the next student question."""
    prompt = build_tester_prompt()
    llm = get_llm(temperature=0.5)

    chain = (
        RunnableParallel(
            tutor_message=RunnableLambda(lambda x: x["tutor_message"]),
            chat_history=RunnableLambda(lambda x: x.get("chat_history", [])),
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


def _resolve_llm_model(settings: Settings) -> str:
    """Return the active LLM model name based on provider settings."""
    if settings.model_provider == "openai":
        return settings.openai_llm_model
    if settings.model_provider == "local":
        return settings.local_llm_model
    return "unknown"


def _save_log(transcript: list[dict[str, str]], max_messages: int, settings: Settings) -> None:
    """Persist the generated tutor/tester transcript with model metadata."""

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _LOG_DIR / f"kg-test-{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    payload = {
        "model_provider": settings.model_provider,
        "llm_model": _resolve_llm_model(settings),
        "max_messages_per_agent": max_messages,
        "message_count": len(transcript),
        "messages": transcript,
    }
    filepath.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> None:
    """
    Generate a test chat between the tutor and the tester.
    """
    settings = get_settings()
    max_messages = settings.test_chat_max_messages_per_agent

    if max_messages <= 0:
        _save_log([], max_messages, settings)
        return

    tutor_chain = build_kg_rag_chain()
    tester_chain = _build_tester_chain()

    tutor_chat_history: list[HumanMessage | AIMessage] = []
    tester_chat_history: list[HumanMessage | AIMessage] = []
    transcript: list[dict[str, str]] = []

    tutor_message = "__START__"
    tester_count = 0
    tutor_count = 0

    try:
        while tester_count < max_messages and tutor_count < max_messages:
            tester_question = tester_chain.invoke(
                {"tutor_message": tutor_message, "chat_history": tester_chat_history}
            ).strip()

            if not tester_question:
                tester_question = "Can you explain that in another way?"

            transcript.append({"role": "tester", "content": tester_question})

            tester_chat_history.append(HumanMessage(content=tutor_message))
            tester_chat_history.append(AIMessage(content=tester_question))
            tester_count += 1

            tutor_answer = tutor_chain.invoke(
                {"question": tester_question, "chat_history": tutor_chat_history},
            ).strip()

            transcript.append({"role": "tutor", "content": tutor_answer})

            tutor_chat_history.append(HumanMessage(content=tester_question))
            tutor_chat_history.append(AIMessage(content=tutor_answer))
            tutor_count += 1

            tutor_message = tutor_answer
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        _save_log(transcript, max_messages, settings)


if __name__ == "__main__":
    main()
