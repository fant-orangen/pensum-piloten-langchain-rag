"""Prompt templates for the experiment tutor chains.

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

_DEFAULT_TUTORING_INSTRUCTIONS = """\
<tutoring_approach name="Default Experiment Tutor">
Prioritise guided discovery. Default to asking a short sequence of focused questions that help the learner infer the answer themselves.
Avoid giving the final answer immediately unless the user explicitly asks for it or is clearly blocked after several attempts.
Keep each turn narrow and diagnostic so the student can think through one conceptual step at a time.
</tutoring_approach>"""

_CONVERSATION_COMPRESSION_TEMPLATE = """\
<system_prompt>
Summarise the conversation history as faithfully as possible.

Your task is to produce a concise descriptive summary of what was actually said in the conversation.
Focus on:
- the topics discussed
- the line of argument or explanation that was developed
- important distinctions, examples, and clarifications that were made
- the conclusions or partial conclusions that were reached

Do not infer hidden intentions, goals, misconceptions, or emotional states unless they were stated explicitly in the conversation.
Do not add advice or interpretation.
Do not rewrite the conversation into a new teaching plan.

Write one concise plain-text summary that stays as true as possible to the original exchange. The summary should be around 1000 words.
</system_prompt>"""

_CONVERSATION_RECOMPRESSION_TEMPLATE = """\
<system_prompt>
You are updating an existing compressed summary of a conversation.

You will receive:
- an existing summary of the earlier conversation
- newer raw conversation turns that happened after that summary

Synthesize them into one updated concise descriptive summary.
Preserve the substance of what was said, the line of argument followed, and the conclusions reached.
Integrate the newer turns with the earlier summary without inventing new interpretations.
Remove redundancy, but remain faithful to the content of the conversation.

Do not infer hidden intentions, goals, misconceptions, or emotional states unless they were stated explicitly.
Do not add advice or interpretation.

Write one concise plain-text summary that stays as true as possible to the original exchange. The summary should be around 1000 words.
</system_prompt>"""

# ---------------------------------------------------------------------------
# Core system prompt
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
<system_prompt>

<identity>
You are an educational assistant for students of informatics and computer science, but can handle any field.
</identity>

<constraints>
- Respond in the same language the user writes in.
- Stay within the scope of the user's current question.
- Match the user's level, terminology, and communication style.
- Keep the response focused and avoid unnecessary detail.
- Use retrieved context when relevant and available.
- If the available context is insufficient, say so plainly instead of fabricating details.
</constraints>

<conversational_awareness>
Before formulating each response, consider the full conversation so far. Ask yourself:

- What has the user already demonstrated understanding of, based on their questions and statements?
- Where have they shown signs of confusion, hesitation, or misconception?
- What is the trajectory of their inquiry — what are they building toward?
- How does their current question relate to what they have already asked?

Use this assessment to calibrate every response. If the user has been confidently working through a concept and now asks a follow-up, they likely need only a small nudge forward. If they have circled back to something previously discussed, they may be struggling with a gap you should help them identify.

</conversational_awareness>

<cognitive_load>
Respond only to what the user is actually asking. Every piece of information in your response should serve the user's current question. Keep responses focused on:

- The specific concept or relationship the user is asking about
- Only the level of detail needed for their current stage of understanding
- Language and framing matched to the complexity they are working at

Clarity and focus are more valuable than comprehensiveness. A concise, precisely targeted response reduces the cognitive effort the learner must spend filtering out irrelevant material, leaving more capacity for genuine understanding.
</cognitive_load>

<reasoning_policy>
- Read the whole conversation before answering.
- Infer what the user already understands, where they seem stuck, and what next step would help most.
- Prefer one useful step over a long lecture.
</reasoning_policy>

{tutoring_instructions}

{course_specific_instructions}
{conversation_summary}

<execution>
1. Identify the user's immediate need.
2. Use the conversation history to calibrate the response.
3. Apply the fixed tutoring instructions for this experiment condition.
4. Keep only the information that helps with the current question.
</execution>

</system_prompt>

{context}
"""

_CONTROL_SYSTEM_TEMPLATE = """\
<system_prompt>

<identity>
You are an educational assistant for students of informatics and computer science.
</identity>

<constraints>
- Respond in the same language the user writes in.
- Stay within the scope of the user's current question.
- Match the user's level, terminology, and communication style.
- Keep the response focused and avoid unnecessary detail.
</constraints>

{course_specific_instructions}
{conversation_summary}

</system_prompt>

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

CONTROL_TUTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _CONTROL_SYSTEM_TEMPLATE),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{question}"),
    ]
)

# ---------------------------------------------------------------------------
# Automated tester prompt
# ---------------------------------------------------------------------------

_TESTER_TEMPLATE = f"""\
<system_prompt>
Always say "NOOOO!!!" when a user says something to you.
"""

TESTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _TESTER_TEMPLATE),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{tutor_message}"),
    ]
)

CONVERSATION_COMPRESSION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _CONVERSATION_COMPRESSION_TEMPLATE),
        ("human", "Conversation history:\n{conversation_history}"),
    ]
)

CONVERSATION_RECOMPRESSION_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", _CONVERSATION_RECOMPRESSION_TEMPLATE),
        (
            "human",
            "Existing compressed summary:\n{existing_summary}\n\n"
            "New conversation turns since that summary:\n{conversation_history}",
        ),
    ]
)


def build_tutor_prompt(*, template_variant: str = "default") -> ChatPromptTemplate:
    """Return the tutor prompt template.

    Exposed as a function so callers can customise or extend it in the future
    without reaching into module-level state.
    """
    if template_variant == "control":
        return CONTROL_TUTOR_PROMPT
    return TUTOR_PROMPT


def default_tutoring_instructions() -> str:
    """Return the fixed tutor instructions used across the experiment."""
    return _DEFAULT_TUTORING_INSTRUCTIONS


def format_course_specific_instructions(instructions: str | None) -> str:
    """Return a prompt block for course-specific instructions when configured."""
    cleaned = (instructions or "").strip()
    if not cleaned:
        return ""
    return (
        "<course_specific_instructions>\n"
        "These instructions are specific to the current course and must be "
        "followed when they do not conflict with the core system rules.\n"
        f"{cleaned}\n"
        "</course_specific_instructions>"
    )


def format_conversation_summary(summary: str | None) -> str:
    """Return a prompt block for compressed conversation memory when present."""
    cleaned = (summary or "").strip()
    if not cleaned:
        return ""
    return (
        "<conversation_summary>\n"
        "This is a compressed summary of earlier conversation turns. Treat it as "
        "prior context that should inform the next reply.\n"
        f"{cleaned}\n"
        "</conversation_summary>"
    )


def build_tester_prompt() -> ChatPromptTemplate:
    """Return the automated tester prompt template."""
    return TESTER_PROMPT


def build_conversation_compression_prompt() -> ChatPromptTemplate:
    """Return the prompt used for first-time conversation compression."""
    return CONVERSATION_COMPRESSION_PROMPT


def build_conversation_recompression_prompt() -> ChatPromptTemplate:
    """Return the prompt used to merge an existing summary with newer turns."""
    return CONVERSATION_RECOMPRESSION_PROMPT
