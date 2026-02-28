"""Embedded chat page for the main Gradio app."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from textwrap import shorten
from typing import Any

import gradio as gr
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from src.chain import build_rag_chain
from src.retriever import get_retriever
from src.vectorstore import get_vectorstore

_CHAIN_CACHE: Any | None = None
_RETRIEVER_CACHE: Any | None = None


@dataclass(slots=True)
class ChatPageComponents:
    group: gr.Group
    back_button: gr.Button


def _vectorstore_status() -> tuple[bool, str]:
    try:
        vectorstore = get_vectorstore()
        count = vectorstore._collection.count()
    except Exception as exc:
        return (
            False,
            "Klarte ikke å åpne vectorstore. Kjør ingest først:\n"
            "`PYTHONPATH=. python -m scripts.ingest`\n"
            f"Detaljer: {exc}",
        )

    if count <= 0:
        return (
            False,
            "Vectorstore er tom. Kjør ingest først:\n"
            "`PYTHONPATH=. python -m scripts.ingest`",
        )

    return True, f"Vectorstore er klar med {count} lagrede tekstbiter."


def _status_markdown() -> str:
    ready, vectorstore_message = _vectorstore_status()
    badge = "Klar" if ready else "Trenger ingest"
    return f"Status: **{badge}**\n\n{vectorstore_message}"


def _empty_sources_markdown() -> str:
    return "_Ingen kilder for dette svaret ennå._"


def _get_chain():
    global _CHAIN_CACHE
    if _CHAIN_CACHE is None:
        _CHAIN_CACHE = build_rag_chain()
    return _CHAIN_CACHE


def _get_retriever():
    global _RETRIEVER_CACHE
    if _RETRIEVER_CACHE is None:
        _RETRIEVER_CACHE = get_retriever()
    return _RETRIEVER_CACHE


def _to_langchain_history(
    history: Sequence[dict[str, Any]] | None,
) -> list[HumanMessage | AIMessage]:
    messages: list[HumanMessage | AIMessage] = []
    if not history:
        return messages

    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if not isinstance(content, str) or not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _display_title(doc: Document) -> str:
    raw_title = doc.metadata.get("source_file")
    if not raw_title or not isinstance(raw_title, str):
        source_path = doc.metadata.get("source_path")
        if isinstance(source_path, str) and source_path.strip():
            raw_title = Path(source_path).name
        else:
            return "Pensum"

    title = raw_title.strip().replace("_", " ")
    if title.lower().endswith(".pdf"):
        title = title[:-4]
    return title or "Pensum"


def _render_sources_markdown(docs: list[Document]) -> str:
    if not docs:
        return _empty_sources_markdown()

    lines: list[str] = []
    for rank, doc in enumerate(docs, 1):
        raw_page = doc.metadata.get("page")
        if raw_page == 0:
            page = "0"
        else:
            page_str = "" if raw_page is None else str(raw_page).strip()
            page = page_str if page_str else "?"

        title = _display_title(doc)
        excerpt = shorten(" ".join(doc.page_content.split()), width=900, placeholder="…")

        lines.append(f"### Kilde {rank} - {title} (s. {page})")
        lines.append("")
        lines.append("> " + excerpt.replace("\n", "\n> "))
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _chat(
    user_message: str,
    history: list[dict[str, Any]] | None,
):
    history = history or []
    text = (user_message or "").strip()
    if not text:
        return "", history, _status_markdown(), _empty_sources_markdown()

    ready, vectorstore_message = _vectorstore_status()
    if not ready:
        error_message = (
            "Kan ikke svare ennå fordi vectorstore ikke er klar.\n\n"
            f"{vectorstore_message}"
        )
        return (
            "",
            history
            + [
                {"role": "user", "content": text},
                {"role": "assistant", "content": error_message},
            ],
            _status_markdown(),
            _empty_sources_markdown(),
        )

    docs: list[Document] = []
    try:
        retrieved_docs = _get_retriever().invoke(text)
        if isinstance(retrieved_docs, list):
            docs = [doc for doc in retrieved_docs if isinstance(doc, Document)]
        answer = _get_chain().invoke(
            {
                "question": text,
                "chat_history": _to_langchain_history(history),
            }
        )
    except Exception as exc:
        answer = (
            "Det oppstod en feil under generering av svar.\n\n"
            f"Detaljer: {exc}"
        )
        docs = []

    updated_history = history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": str(answer)},
    ]
    return "", updated_history, _status_markdown(), _render_sources_markdown(docs)


def _clear():
    return [], _status_markdown(), "", _empty_sources_markdown()


def build_chat_page(*, visible: bool) -> ChatPageComponents:
    with gr.Group(visible=visible) as group:
        gr.Markdown("# Chat")
        gr.Markdown("Chat med tutor (RAG).")

        status = gr.Markdown(_status_markdown())
        chatbot = gr.Chatbot(type="messages", height=700, label="Chat")
        message = gr.Textbox(
            label="Melding",
            placeholder="Spør om minnehåndtering, paging, scheduling, ...",
            lines=2,
        )
        with gr.Accordion("Kilder", open=False):
            sources = gr.Markdown(_empty_sources_markdown())

        with gr.Row():
            send_button = gr.Button("Send", variant="primary")
            clear_button = gr.Button("Tøm chat")
            back_button = gr.Button("Tilbake")

    send_button.click(
        fn=_chat,
        inputs=[message, chatbot],
        outputs=[message, chatbot, status, sources],
    )
    clear_button.click(
        fn=_clear,
        inputs=None,
        outputs=[chatbot, status, message, sources],
    )

    return ChatPageComponents(group=group, back_button=back_button)
