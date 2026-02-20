"""Prompt templates for the Socratic tutoring RAG chain.

The pedagogical strategy is deliberate: the system must *guide* the student
toward understanding rather than hand over answers.  Key techniques encoded in
the prompt:

  1. Scaffolded questioning  — break the problem into smaller, approachable
     parts and ask the student to reason about each one.
  2. Formative feedback      — acknowledge what the student already knows and
     build on it.
  3. Source grounding         — only use information present in the retrieved
     context to avoid hallucination.
  4. Metacognitive prompts   — encourage the student to reflect on *how* they
     are thinking, not just *what* they are thinking.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ---------------------------------------------------------------------------
# Core system prompt
# ---------------------------------------------------------------------------

# TODO: これを修正して
_SYSTEM_TEMPLATE = """\
You are a direct-instruction tutor for university students. Your goal is to
explain concepts clearly and efficiently while staying grounded in the provided
course material.

Teaching guidelines
Start with a short, direct explanation of the concept.
Use structure: definition, intuition, example, common mistake.
Keep explanations concise and easy to scan.
Use only the retrieved course context below. If context is insufficient,
say what is missing.
End with 1-2 quick comprehension checks.

Retrieved course material

{context}
"""

# ---------------------------------------------------------------------------
# Prompt objects
# ---------------------------------------------------------------------------

TUTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_TEMPLATE),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{question}"),
    ]
)


def build_tutor_prompt() -> ChatPromptTemplate:
    """Return the tutor prompt template.

    Exposed as a function so callers can customise or extend it in the future
    without reaching into module-level state.
    """
    return TUTOR_PROMPT
