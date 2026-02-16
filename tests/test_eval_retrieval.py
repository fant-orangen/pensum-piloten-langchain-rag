from pathlib import Path

from langchain_core.documents import Document

from scripts.eval_retrieval import _is_relevant, _load_examples


def test_load_eval_examples() -> None:
    dataset = Path(__file__).resolve().parents[1] / "data" / "eval" / "retrieval_eval.jsonl"
    examples = _load_examples(dataset, limit=3)
    assert len(examples) == 3
    assert examples[0].question


def test_is_relevant_matches_source_hint() -> None:
    doc = Document(
        page_content="Virtual memory maps addresses.",
        metadata={"source_file": "OS Principles Practice Vol 1.pdf", "chunk_id": "x"},
    )
    examples = _load_examples(
        Path(__file__).resolve().parents[1] / "data" / "eval" / "retrieval_eval.jsonl",
        limit=1,
    )
    assert _is_relevant(doc, examples[0]) is True
