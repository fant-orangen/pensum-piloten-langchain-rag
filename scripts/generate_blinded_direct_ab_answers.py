"""Generate blinded A/B answer files for prompt or retrieval evaluation.

Usage:
    python -m scripts.generate_blinded_direct_ab_answers --input data/questions.txt
    python -m scripts.generate_blinded_direct_ab_answers --input data/questions.txt \
        --comparison rag-vs-no-rag

The comparison mirrors the current course experiment routing:
- direct_system_prompt: no retrieval, default/full tutor system prompt
- no_rag_control: no retrieval, stripped control prompt
- rag: KG-RAG retrieval, default/full tutor system prompt
- no_rag: no retrieval, default/full tutor system prompt
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

AnswerSource = Literal["direct_system_prompt", "no_rag_control", "rag", "no_rag"]
AnswerLabel = Literal["A", "B"]
ComparisonMode = Literal["direct-vs-control", "rag-vs-no-rag"]

DEFAULT_DIRECT_PROMPT_VARIANT = "default"
DEFAULT_NO_RAG_PROMPT_VARIANT = "control"
DEFAULT_RAG_NO_RAG_PROMPT_VARIANT = "default"

_QUESTION_PATTERN = re.compile(r"(?ms)^\s*(\d+)[.)]\s+(.+?)(?=^\s*\d+[.)]\s+|\Z)")


@dataclass(frozen=True, slots=True)
class Question:
    number: int
    text: str


@dataclass(frozen=True, slots=True)
class GeneratedAnswerPair:
    question: Question
    answer_a: str
    answer_b: str
    source_a: AnswerSource
    source_b: AnswerSource
    primary_latency_seconds: float
    baseline_latency_seconds: float
    primary_source: AnswerSource
    baseline_source: AnswerSource
    primary_prompt_variant: str
    baseline_prompt_variant: str
    comparison: ComparisonMode
    chroma_collection: str | None = None
    graph_scope: str | None = None


def parse_questions(raw_text: str) -> list[Question]:
    """Parse numbered questions from a plain text document."""
    questions: list[Question] = []
    for match in _QUESTION_PATTERN.finditer(raw_text):
        number = int(match.group(1))
        text = " ".join(match.group(2).split())
        if text:
            questions.append(Question(number=number, text=text))
    return questions


def build_direct_label_plan(question_count: int, *, seed: int | None) -> list[AnswerLabel]:
    """Return a shuffled, balanced plan for which label receives the direct answer."""
    return build_primary_label_plan(question_count, seed=seed)


def build_primary_label_plan(question_count: int, *, seed: int | None) -> list[AnswerLabel]:
    """Return a shuffled, balanced plan for which label receives the primary answer."""
    direct_labels: list[AnswerLabel] = ["A"] * (question_count // 2)
    direct_labels.extend(["B"] * (question_count - len(direct_labels)))
    rng = random.Random(seed)
    rng.shuffle(direct_labels)
    return direct_labels


def format_blinded_answers(records: list[GeneratedAnswerPair]) -> str:
    """Format generated records as evaluator-facing blinded text."""
    blocks: list[str] = []
    for record in records:
        blocks.append(
            "\n".join(
                [
                    f"{record.question.number}. {record.question.text}",
                    "A)",
                    record.answer_a.strip(),
                    "B)",
                    record.answer_b.strip(),
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def _source_label(records_source_a: AnswerSource, wanted: AnswerSource) -> AnswerLabel:
    return "A" if records_source_a == wanted else "B"


def _label_if_present(record: GeneratedAnswerPair, wanted: AnswerSource) -> str:
    if record.source_a == wanted:
        return "A"
    if record.source_b == wanted:
        return "B"
    return ""


def write_answer_key(records: list[GeneratedAnswerPair], path: Path) -> None:
    """Write the A/B label mapping as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "question_number",
                "question",
                "comparison",
                "answer_a_source",
                "answer_b_source",
                "primary_source",
                "baseline_source",
                "primary_label",
                "baseline_label",
                "direct_label",
                "control_label",
                "rag_label",
                "no_rag_label",
                "primary_latency_seconds",
                "baseline_latency_seconds",
                "primary_prompt_variant",
                "baseline_prompt_variant",
                "chroma_collection",
                "graph_scope",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "question_number": record.question.number,
                    "question": record.question.text,
                    "comparison": record.comparison,
                    "answer_a_source": record.source_a,
                    "answer_b_source": record.source_b,
                    "primary_source": record.primary_source,
                    "baseline_source": record.baseline_source,
                    "primary_label": _source_label(record.source_a, record.primary_source),
                    "baseline_label": _source_label(record.source_a, record.baseline_source),
                    "direct_label": _label_if_present(record, "direct_system_prompt"),
                    "control_label": _label_if_present(record, "no_rag_control"),
                    "rag_label": _label_if_present(record, "rag"),
                    "no_rag_label": _label_if_present(record, "no_rag"),
                    "primary_latency_seconds": f"{record.primary_latency_seconds:.3f}",
                    "baseline_latency_seconds": f"{record.baseline_latency_seconds:.3f}",
                    "primary_prompt_variant": record.primary_prompt_variant,
                    "baseline_prompt_variant": record.baseline_prompt_variant,
                    "chroma_collection": record.chroma_collection or "",
                    "graph_scope": record.graph_scope or "",
                }
            )


def write_direct_label_list(records: list[GeneratedAnswerPair], path: Path) -> None:
    """Write the direct-system-prompt answer labels in question order, e.g. BBAA."""
    write_primary_label_list(records, path)


def write_primary_label_list(records: list[GeneratedAnswerPair], path: Path) -> None:
    """Write the primary answer labels in question order, e.g. BBAA."""
    labels = [_source_label(record.source_a, record.primary_source) for record in records]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(labels) + "\n", encoding="utf-8")


def _invoke_chain(chain: Any, question: str) -> str:
    answer = chain.invoke(
        {
            "question": question,
            "chat_history": [],
            "course_specific_instructions": None,
            "conversation_summary": None,
        }
    )
    return str(answer).strip()


def generate_answer_pairs(
    questions: list[Question],
    *,
    seed: int | None,
    continue_on_error: bool,
    comparison: ComparisonMode = "direct-vs-control",
    direct_prompt_variant: str = DEFAULT_DIRECT_PROMPT_VARIANT,
    no_rag_prompt_variant: str | None = None,
    chroma_collection: str | None = None,
    graph_scope: str | None = None,
) -> list[GeneratedAnswerPair]:
    """Generate answers for the selected comparison and assign blinded labels."""
    if no_rag_prompt_variant is None:
        no_rag_prompt_variant = (
            DEFAULT_RAG_NO_RAG_PROMPT_VARIANT
            if comparison == "rag-vs-no-rag"
            else DEFAULT_NO_RAG_PROMPT_VARIANT
        )

    primary_source, baseline_source, primary_chain, baseline_chain = _build_comparison_chains(
        comparison=comparison,
        direct_prompt_variant=direct_prompt_variant,
        no_rag_prompt_variant=no_rag_prompt_variant,
        chroma_collection=chroma_collection,
        graph_scope=graph_scope,
    )
    primary_label_plan = build_primary_label_plan(len(questions), seed=seed)

    records: list[GeneratedAnswerPair] = []
    for index, question in enumerate(questions, start=1):
        print(f"Generating answers for question {index}/{len(questions)}...", flush=True)

        try:
            primary_start = time.perf_counter()
            primary_answer = _invoke_chain(primary_chain, question.text)
            primary_latency = time.perf_counter() - primary_start

            baseline_start = time.perf_counter()
            baseline_answer = _invoke_chain(baseline_chain, question.text)
            baseline_latency = time.perf_counter() - baseline_start
        except Exception as exc:
            if not continue_on_error:
                raise
            primary_answer = f"[Generation failed: {exc}]"
            baseline_answer = f"[Generation failed: {exc}]"
            primary_latency = 0.0
            baseline_latency = 0.0

        primary_label = primary_label_plan[index - 1]
        if primary_label == "A":
            answer_a = primary_answer
            answer_b = baseline_answer
            source_a = primary_source
            source_b = baseline_source
        else:
            answer_a = baseline_answer
            answer_b = primary_answer
            source_a = baseline_source
            source_b = primary_source

        records.append(
            GeneratedAnswerPair(
                question=question,
                answer_a=answer_a,
                answer_b=answer_b,
                source_a=source_a,
                source_b=source_b,
                primary_latency_seconds=primary_latency,
                baseline_latency_seconds=baseline_latency,
                primary_source=primary_source,
                baseline_source=baseline_source,
                primary_prompt_variant=direct_prompt_variant,
                baseline_prompt_variant=no_rag_prompt_variant,
                comparison=comparison,
                chroma_collection=chroma_collection,
                graph_scope=graph_scope,
            )
        )

    return records


def _build_comparison_chains(
    *,
    comparison: ComparisonMode,
    direct_prompt_variant: str,
    no_rag_prompt_variant: str,
    chroma_collection: str | None,
    graph_scope: str | None,
) -> tuple[AnswerSource, AnswerSource, Any, Any]:
    from src.chain.no_rag_chain import build_no_rag_chain

    if comparison == "rag-vs-no-rag":
        from src.chain.kg_rag_chain import build_kg_rag_chain

        rag_chain = build_kg_rag_chain(
            chroma_collection=chroma_collection,
            graph_scope=graph_scope,
            prompt_variant=direct_prompt_variant,
        )
        no_rag_chain = build_no_rag_chain(prompt_variant=no_rag_prompt_variant)
        return "rag", "no_rag", rag_chain, no_rag_chain

    direct_chain = build_no_rag_chain(prompt_variant=direct_prompt_variant)
    control_chain = build_no_rag_chain(prompt_variant=no_rag_prompt_variant)
    return "direct_system_prompt", "no_rag_control", direct_chain, control_chain


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate blinded A/B answer files for prompt-only or RAG-vs-no-RAG "
            "evaluation."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Plain text file with numbered questions, e.g. '1. What is ...?'",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/ab_test/direct_blinded_answers.txt"),
        help="Evaluator-facing blinded text output.",
    )
    parser.add_argument(
        "--comparison",
        choices=["direct-vs-control", "rag-vs-no-rag"],
        default="direct-vs-control",
        help=(
            "Comparison to run. Use rag-vs-no-rag to compare KG-RAG retrieval "
            "against no retrieval."
        ),
    )
    parser.add_argument(
        "--key-output",
        type=Path,
        default=Path("data/ab_test/direct_answer_key.csv"),
        help="CSV answer key showing which label belongs to each condition.",
    )
    parser.add_argument(
        "--direct-label-output",
        "--primary-label-output",
        dest="primary_label_output",
        type=Path,
        default=Path("data/ab_test/direct_labels.txt"),
        help="Plain text list of primary-condition labels in question order, e.g. BBAA.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for reproducible A/B label randomization.",
    )
    parser.add_argument(
        "--direct-prompt-variant",
        default=DEFAULT_DIRECT_PROMPT_VARIANT,
        help="Prompt variant used for the primary condition.",
    )
    parser.add_argument(
        "--no-rag-prompt-variant",
        default=None,
        help=(
            "Prompt variant used for the baseline condition. Defaults to control for "
            "direct-vs-control and default for rag-vs-no-rag."
        ),
    )
    parser.add_argument(
        "--chroma-collection",
        default=None,
        help=(
            "Optional Chroma collection for rag-vs-no-rag. Defaults to the global "
            "configured collection."
        ),
    )
    parser.add_argument(
        "--graph-scope",
        default=None,
        help=(
            "Optional Neo4j graph scope for rag-vs-no-rag. Defaults to the same value "
            "as --chroma-collection when provided."
        ),
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Keep writing output if a question fails instead of aborting the run.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    no_rag_prompt_variant = args.no_rag_prompt_variant
    if no_rag_prompt_variant is None:
        no_rag_prompt_variant = (
            DEFAULT_RAG_NO_RAG_PROMPT_VARIANT
            if args.comparison == "rag-vs-no-rag"
            else DEFAULT_NO_RAG_PROMPT_VARIANT
        )
    graph_scope = args.graph_scope
    if graph_scope is None and args.comparison == "rag-vs-no-rag":
        graph_scope = args.chroma_collection

    raw_text = args.input.read_text(encoding="utf-8")
    questions = parse_questions(raw_text)
    if not questions:
        raise SystemExit(f"No numbered questions found in {args.input}.")

    records = generate_answer_pairs(
        questions,
        seed=args.seed,
        continue_on_error=args.continue_on_error,
        comparison=args.comparison,
        direct_prompt_variant=args.direct_prompt_variant,
        no_rag_prompt_variant=no_rag_prompt_variant,
        chroma_collection=args.chroma_collection,
        graph_scope=graph_scope,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(format_blinded_answers(records), encoding="utf-8")
    write_answer_key(records, args.key_output)
    write_primary_label_list(records, args.primary_label_output)

    print(f"Wrote blinded answers to {args.output}")
    print(f"Wrote answer key to {args.key_output}")
    print(f"Wrote primary label list to {args.primary_label_output}")


if __name__ == "__main__":
    main()
