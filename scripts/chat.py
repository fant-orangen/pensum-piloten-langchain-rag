"""CLI chat — interactive conversation with the Socratic tutor in the terminal.

Usage:
    python -m scripts.chat
"""

import sys

from langchain_core.messages import HumanMessage, AIMessage

from src.chain import build_rag_chain

# ANSI colour codes
_BLUE = "\033[94m"
_GREEN = "\033[92m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def main() -> None:
    print(f"\n{_BOLD}Pensum Piloten — Socratic Tutor{_RESET}")
    print("Type your question and press Enter. Type 'quit' or 'exit' to stop.\n")

    chain = build_rag_chain()
    chat_history: list[HumanMessage | AIMessage] = []

    while True:
        try:
            user_input = input(f"{_GREEN}{_BOLD}User:{_RESET} ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if user_input.strip().lower() in {"quit", "exit", "q"}:
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
