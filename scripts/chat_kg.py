"""CLI chat with KG-RAG — interactive conversation using knowledge graph-expanded retrieval.

Usage:
    python -m scripts.chat_kg
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage

from src.chain.kg_rag_chain import build_kg_rag_chain

_LOG_DIR = Path("data/chat_logs")

# ANSI colour codes
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _save_log(chat_history: list[HumanMessage | AIMessage]) -> None:
    if not chat_history:
        return
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _LOG_DIR / f"kg-{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
    log = [{"role": "human" if isinstance(m, HumanMessage) else "ai", "content": m.content}
           for m in chat_history]
    filepath.write_text(json.dumps(log, indent=2, ensure_ascii=False))


def main() -> None:
    print(f"\n{_BOLD}Pensum Piloten — Socratic Tutor (KG-RAG){_RESET}")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    chain = build_kg_rag_chain()
    chat_history: list[HumanMessage | AIMessage] = []

    while True:
        try:
            user_input = input(f"{_GREEN}{_BOLD}User:{_RESET} ")
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

        answer = chain.invoke({"question": user_input, "chat_history": chat_history})

        print(f"{_BLUE}{_BOLD}Tutor:{_RESET} {answer}\n")

        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=answer))


if __name__ == "__main__":
    main()
