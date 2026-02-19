"""Prompt templates for the tutoring RAG chain."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.prompts.modes import DEFAULT_MODE_KEY, get_mode_prompt


def build_tutor_prompt(system_prompt: str | None = None) -> ChatPromptTemplate:
    """Return the tutor prompt template.

    If no system prompt is supplied, the default Socratic mode is used.
    """
    resolved_system_prompt = system_prompt or get_mode_prompt(DEFAULT_MODE_KEY)
    return ChatPromptTemplate.from_messages(
        [
            ("system", resolved_system_prompt),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{question}"),
        ]
    )


# Backwards-compatible default prompt object for existing imports.
TUTOR_PROMPT = build_tutor_prompt()
