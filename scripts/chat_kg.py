"""CLI chat with KG-RAG — interactive conversation using knowledge graph-expanded retrieval.

Usage:
    python -m scripts.chat_kg
    python -m scripts.chat_kg --debug   # print retrieved chunks before each response
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage

from src.chain.kg_rag_chain import build_kg_rag_chain

_LOG_DIR = Path("data/chat_logs")

# ANSI colour codes
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


class _ChunkDebugHandler(BaseCallbackHandler):
    """Callback that prints retrieved chunks to stdout."""

    def on_retriever_end(self, documents: list[Document], **kwargs: Any) -> None:
        """Print retrieved documents after a retriever run in debug mode."""

        print(f"\n{_YELLOW}{_BOLD}[DEBUG] Retrieved {len(documents)} chunk(s):{_RESET}")
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source_path") or doc.metadata.get("source_file", "unknown")
            chunk_id = doc.metadata.get("chunk_id", "?")
            page = doc.metadata.get("page", "")
            page_str = f", p. {page}" if page else ""
            print(f"\n  {_BOLD}#{i}{_RESET} {_DIM}{source} [{chunk_id}]{page_str}{_RESET}")
            print(f"{_DIM}{'─' * 60}{_RESET}")
            print(doc.page_content)
            print(f"{_DIM}{'─' * 60}{_RESET}")
        print()


def _save_log(chat_history: list[HumanMessage | AIMessage]) -> None:
    """Write the KG chat transcript to data/chat_logs if it is non-empty."""

    if not chat_history:
        return
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _LOG_DIR / f"kg-{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    log = [{"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
           for m in chat_history]
    filepath.write_text(json.dumps(log, indent=2, ensure_ascii=False))


def main() -> None:
    """Run an interactive terminal chat session against the KG-RAG chain."""

    debug = "--debug" in sys.argv

    print(f"\n{_BOLD}Pensum Piloten — Socratic Tutor (KG-RAG){_RESET}")
    if debug:
        print(f"{_YELLOW}[DEBUG mode enabled — retrieved chunks will be shown]{_RESET}")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    chain = build_kg_rag_chain()
    chat_history: list[HumanMessage | AIMessage] = [] # Differentiate between human and AI messages
    callbacks = [_ChunkDebugHandler()] if debug else []

    while True:
        try:
            # Print a styled label separately so readline gets a plain prompt.
            # Passing ANSI escapes directly to input() can break cursor/wrap math.
            print(f"{_GREEN}{_BOLD}User:{_RESET} ", end="", flush=True)
            user_input = input()
        except (EOFError, KeyboardInterrupt):
            _save_log(chat_history)
            print("\nGoodbye!")
            sys.exit(0)

        if user_input.strip().lower() in {"quit", "exit", "q"}:
            _save_log(chat_history)
            print("Goodbye!")
            break

        if not user_input.strip():
            continue

        answer = chain.invoke(
            {"question": user_input, "chat_history": chat_history},
            config={"callbacks": callbacks},
        )

        print(f"{_BLUE}{_BOLD}Tutor:{_RESET} {answer}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=answer))


if __name__ == "__main__":
    main()
