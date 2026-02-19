"""Gradio web app for chatting with the RAG tutor.

Run:
    PYTHONPATH=. python -m scripts.gradio_app
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from textwrap import shorten
from typing import Any

import gradio as gr
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from src.chain import build_rag_chain_with_sources
from src.prompts import DEFAULT_MODE_KEY, MODE_LABELS, MODE_PROMPTS
from src.vectorstore import get_vectorstore

_LABEL_TO_MODE = {label: key for key, label in MODE_LABELS.items()}
_MODE_CHOICES = [MODE_LABELS[key] for key in MODE_LABELS]
_DEFAULT_MODE_LABEL = MODE_LABELS[DEFAULT_MODE_KEY]
_CHAIN_CACHE: dict[str, Any] = {}


def _vectorstore_status() -> tuple[bool, str]:
    """Return readiness status and a human-readable message."""
    try:
        vectorstore = get_vectorstore()
        count = vectorstore._collection.count()
    except Exception as exc:
        return (
            False,
            "Unable to open vectorstore. Run ingestion first:\n"
            "`PYTHONPATH=. python -m scripts.ingest`\n"
            f"Details: {exc}",
        )

    if count <= 0:
        return (
            False,
            "Vectorstore is empty. Run ingestion first:\n"
            "`PYTHONPATH=. python -m scripts.ingest`",
        )

    return True, f"Vectorstore ready with {count} stored chunks."


def _get_chain(mode_key: str):
    """Build/cache one chain per teaching mode."""
    if mode_key in _CHAIN_CACHE:
        return _CHAIN_CACHE[mode_key]

    prompt = MODE_PROMPTS.get(mode_key, MODE_PROMPTS[DEFAULT_MODE_KEY])
    chain = build_rag_chain_with_sources(system_prompt=prompt)
    _CHAIN_CACHE[mode_key] = chain
    return chain


def _to_langchain_history(
    history: Sequence[Sequence[str | None]] | None,
) -> list[HumanMessage | AIMessage]:
    """Convert Gradio chat history (user, bot pairs) into LangChain messages."""
    messages: list[HumanMessage | AIMessage] = []
    if not history:
        return messages

    for turn in history:
        if not turn:
            continue
        user = turn[0] if len(turn) > 0 else None
        bot = turn[1] if len(turn) > 1 else None
        if user:
            messages.append(HumanMessage(content=user))
        if bot:
            messages.append(AIMessage(content=bot))
    return messages


def _mode_status_text(mode_label: str, vectorstore_message: str) -> str:
    return f"Mode: **{mode_label}**\n\n{vectorstore_message}"


def _status_markdown(mode_label: str) -> str:
    ready, vectorstore_message = _vectorstore_status()
    badge = "Ready" if ready else "Needs ingestion"
    return f"Status: **{badge}**\n\n{_mode_status_text(mode_label, vectorstore_message)}"


def _empty_sources_markdown() -> str:
    return "_No sources for this response yet._"


def _format_page(raw_page: object) -> str:
    if raw_page == 0:
        return "0"
    if raw_page is None:
        return "-"
    page_str = str(raw_page).strip()
    return page_str if page_str else "-"


def _format_source_id(doc: Document) -> str:
    source = doc.metadata.get("source_file") or doc.metadata.get("source_path") or "unknown"
    page = _format_page(doc.metadata.get("page"))
    chunk_ref = doc.metadata.get("chunk_id")
    if not chunk_ref:
        chunk_index = doc.metadata.get("chunk_index")
        chunk_ref = f"c{chunk_index}" if chunk_index is not None else "-"
    return f"{source} | p={page} | id={chunk_ref}"


def _render_sources_markdown(docs: list[Document]) -> str:
    if not docs:
        return _empty_sources_markdown()

    lines: list[str] = ["Retrieved sources:"]
    for rank, doc in enumerate(docs, 1):
        preview = shorten(" ".join(doc.page_content.split()), width=220, placeholder="…")
        lines.append(f"{rank}. **{_format_source_id(doc)}**")
        lines.append(f"   {preview}")
    return "\n".join(lines)


def _extract_answer_and_docs(result: object) -> tuple[str, list[Document]]:
    if isinstance(result, dict):
        answer = str(result.get("answer", ""))
        docs = result.get("docs")
        if isinstance(docs, list):
            return answer, [d for d in docs if isinstance(d, Document)]
        return answer, []
    return str(result), []


def _chat(
    user_message: str,
    history: list[tuple[str | None, str | None]] | None,
    mode_label: str,
):
    history = history or []
    text = (user_message or "").strip()
    if not text:
        return "", history, _status_markdown(mode_label), _empty_sources_markdown()

    mode_key = _LABEL_TO_MODE.get(mode_label, DEFAULT_MODE_KEY)
    ready, vectorstore_message = _vectorstore_status()
    if not ready:
        error_msg = (
            "Cannot answer yet because the vectorstore is not ready.\n\n"
            f"{vectorstore_message}"
        )
        return (
            "",
            history + [(text, error_msg)],
            _status_markdown(mode_label),
            _empty_sources_markdown(),
        )

    docs: list[Document] = []
    try:
        chain = _get_chain(mode_key)
        chat_history = _to_langchain_history(history)
        result = chain.invoke({"question": text, "chat_history": chat_history})
        answer, docs = _extract_answer_and_docs(result)
    except Exception as exc:
        answer = (
            "An error occurred while generating a response.\n\n"
            f"Details: {exc}"
        )
        docs = []

    updated_history = history + [(text, str(answer))]
    return "", updated_history, _status_markdown(mode_label), _render_sources_markdown(docs)


def _clear(mode_label: str):
    return [], _status_markdown(mode_label), "", _empty_sources_markdown()


def _on_mode_change(mode_label: str):
    return [], _status_markdown(mode_label), "", _empty_sources_markdown()


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Pensum Piloten - Tutor", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# Pensum Piloten - RAG Tutor\n"
            "Choose a teaching mode and chat with the tutor."
        )

        mode = gr.Radio(
            choices=_MODE_CHOICES,
            value=_DEFAULT_MODE_LABEL,
            label="Teaching mode",
        )
        status = gr.Markdown(_status_markdown(_DEFAULT_MODE_LABEL))

        chatbot = gr.Chatbot(label="Tutor chat", height=500, type="tuples")
        message = gr.Textbox(
            label="Your message",
            placeholder="Ask about memory access, paging, scheduling, ...",
            lines=2,
        )
        with gr.Accordion("Sources", open=False):
            sources = gr.Markdown(_empty_sources_markdown())

        with gr.Row():
            send_button = gr.Button("Send", variant="primary")
            clear_button = gr.Button("Clear chat")

        send_button.click(
            fn=_chat,
            inputs=[message, chatbot, mode],
            outputs=[message, chatbot, status, sources],
        )
        message.submit(
            fn=_chat,
            inputs=[message, chatbot, mode],
            outputs=[message, chatbot, status, sources],
        )
        clear_button.click(
            fn=_clear,
            inputs=[mode],
            outputs=[chatbot, status, message, sources],
        )

        mode.change(
            fn=_on_mode_change,
            inputs=[mode],
            outputs=[chatbot, status, message, sources],
        )

    return demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the Gradio RAG tutor UI.")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    demo = build_demo()
    demo.launch(server_name=args.host, server_port=args.port)


if __name__ == "__main__":
    main()
