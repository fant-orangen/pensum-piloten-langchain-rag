import os

from src.chain.rag_chain import _apply_grounding
from src.config import get_settings


def test_grounding_disabled_returns_answer() -> None:
    os.environ["GROUNDING_ENABLED"] = "false"
    get_settings.cache_clear()
    answer = "Virtual memory maps addresses to physical memory."
    result = _apply_grounding(
        {
            "answer": answer,
            "context": "Virtual memory maps addresses to physical memory via page tables.",
            "question": "What is virtual memory?",
        }
    )
    assert result == answer


def test_grounding_note_appends_warning_when_unsupported() -> None:
    os.environ["GROUNDING_ENABLED"] = "true"
    os.environ["GROUNDING_MODE"] = "note"
    get_settings.cache_clear()
    result = _apply_grounding(
        {
            "answer": (
                "Virtual memory maps addresses to physical memory. "
                "Penguins can pilot spacecraft in orbit."
            ),
            "context": "Virtual memory maps addresses to physical memory through translation.",
            "question": "Explain virtual memory.",
        }
    )
    assert "not be fully supported" in result


def test_grounding_prune_removes_unsupported() -> None:
    os.environ["GROUNDING_ENABLED"] = "true"
    os.environ["GROUNDING_MODE"] = "prune"
    get_settings.cache_clear()
    result = _apply_grounding(
        {
            "answer": (
                "Virtual memory maps addresses to physical memory. "
                "Penguins can pilot spacecraft in orbit."
            ),
            "context": "Virtual memory maps addresses to physical memory through translation.",
            "question": "Explain virtual memory.",
        }
    )
    assert "Penguins can pilot spacecraft in orbit." not in result
    assert "Virtual memory maps addresses to physical memory." in result
