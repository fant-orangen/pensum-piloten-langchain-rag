"""Judge anonymized RAG answers with the configured project LLM.

Usage:
    python -m scripts.judge_anonymized_answers \
        --run-dir data/retrieval_review/run_20260510_120000 \
        --limit 5

The raw judgment JSONL stays blinded: it contains the anonymized method label,
not the actual retrieval method. The summary files join with ``review_key.csv``
after judging.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_RUBRIC_FIELDS = [
    "correctness",
    "relevance",
    "clarity",
    "pedagogical_usefulness",
    "faithfulness_to_chunks",
    "overall",
]


@dataclass(frozen=True, slots=True)
class ReviewAnswer:
    query_id: str
    question: str
    method_label: str
    answer: str
    chunks: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class AnswerJudgment:
    correctness: int
    relevance: int
    clarity: int
    pedagogical_usefulness: int
    faithfulness_to_chunks: int
    overall: int
    short_explanation: str


@dataclass(frozen=True, slots=True)
class JudgmentRecord:
    query_id: str
    question: str
    method_label: str
    judgment: AnswerJudgment
    judge_model: str


@dataclass(frozen=True, slots=True)
class MethodJudgmentSummary:
    method: str
    count: int
    correctness: float
    relevance: float
    clarity: float
    pedagogical_usefulness: float
    faithfulness_to_chunks: float
    overall: float


def load_review_answers(path: Path, *, limit: int | None = None) -> list[ReviewAnswer]:
    """Load anonymized answer records from review_records.jsonl."""
    answers: list[ReviewAnswer] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            answers.append(
                ReviewAnswer(
                    query_id=_required_string(payload, "query_id", line_number),
                    question=_required_string(payload, "question", line_number),
                    method_label=_required_string(payload, "method_label", line_number),
                    answer=_required_string(payload, "answer", line_number),
                    chunks=_required_chunks(payload, line_number),
                )
            )
            if limit is not None and len(answers) >= limit:
                break
    return answers


def load_review_key(path: Path) -> dict[tuple[str, str], str]:
    """Load mapping from anonymized labels to actual methods."""
    mapping: dict[tuple[str, str], str] = {}
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            query_id = str(row.get("query_id", "")).strip()
            method_label = str(row.get("method_label", "")).strip()
            actual_method = str(row.get("actual_method", "")).strip()
            if query_id and method_label and actual_method:
                mapping[(query_id, method_label)] = actual_method
    return mapping


def _required_string(payload: dict[str, Any], key: str, line_number: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Line {line_number} is missing non-empty string field {key!r}.")
    return value.strip()


def _required_chunks(payload: dict[str, Any], line_number: int) -> list[dict[str, Any]]:
    value = payload.get("chunks")
    if not isinstance(value, list):
        raise ValueError(f"Line {line_number} is missing list field 'chunks'.")
    return [chunk for chunk in value if isinstance(chunk, dict)]


def judge_answers(
    answers: list[ReviewAnswer],
    *,
    max_chunk_chars: int,
    continue_on_error: bool,
) -> list[JudgmentRecord]:
    """Judge answer records with the configured LLM."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    from src.models import get_llm

    judge_model = _resolve_judge_model_name()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a careful evaluator for a bachelor thesis RAG experiment. "
                "Judge the answer using only the question, answer, and retrieved chunks. "
                "Return only valid JSON with exactly these keys: correctness, relevance, "
                "clarity, pedagogical_usefulness, faithfulness_to_chunks, overall, "
                "short_explanation. Scores must be integers from 1 to 5, where 1 is poor "
                "and 5 is excellent.",
            ),
            (
                "human",
                "Question:\n{question}\n\nRetrieved chunks:\n{chunks}\n\nAnswer:\n{answer}\n\n"
                "Rubric:\n"
                "- correctness: factual and conceptual correctness.\n"
                "- relevance: answers the user's question directly.\n"
                "- clarity: easy to understand and well structured.\n"
                "- pedagogical_usefulness: helps a student learn, not just memorize.\n"
                "- faithfulness_to_chunks: supported by the retrieved chunks and does not "
                "invent unsupported claims.\n"
                "- overall: holistic quality score.\n\n"
                "Return JSON only.",
            ),
        ]
    )
    chain = prompt | get_llm(temperature=0.0) | StrOutputParser()

    judgments: list[JudgmentRecord] = []
    for index, answer in enumerate(answers, start=1):
        print(f"Judging answer {index}/{len(answers)}...", flush=True)
        try:
            raw_judgment = chain.invoke(
                {
                    "question": answer.question,
                    "chunks": format_chunks_for_prompt(answer.chunks, max_chunk_chars=max_chunk_chars),
                    "answer": answer.answer,
                }
            )
            judgment = parse_judgment_response(raw_judgment)
        except Exception:
            if not continue_on_error:
                raise
            judgment = AnswerJudgment(
                correctness=1,
                relevance=1,
                clarity=1,
                pedagogical_usefulness=1,
                faithfulness_to_chunks=1,
                overall=1,
                short_explanation="[Judging failed]",
            )

        judgments.append(
            JudgmentRecord(
                query_id=answer.query_id,
                question=answer.question,
                method_label=answer.method_label,
                judgment=judgment,
                judge_model=judge_model,
            )
        )
    return judgments


def format_chunks_for_prompt(chunks: list[dict[str, Any]], *, max_chunk_chars: int) -> str:
    """Format retrieved chunks for judge prompting."""
    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        text = str(chunk.get("text", "")).strip()
        if max_chunk_chars > 0 and len(text) > max_chunk_chars:
            text = text[:max_chunk_chars].rstrip() + "\n[truncated]"
        parts.append(
            "\n".join(
                [
                    f"Chunk {index}",
                    f"chunk_id: {chunk.get('chunk_id', '')}",
                    f"source: {chunk.get('source', '')}",
                    f"page: {chunk.get('page', '')}",
                    text,
                ]
            )
        )
    return "\n\n---\n\n".join(parts)


def parse_judgment_response(raw_response: str) -> AnswerJudgment:
    """Parse and validate the LLM's JSON rubric response."""
    payload = _loads_json_object(raw_response)
    scores: dict[str, int] = {}
    for field in _RUBRIC_FIELDS:
        value = payload.get(field)
        if not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"Judgment field {field!r} must be an integer from 1 to 5.")
        scores[field] = value

    explanation = payload.get("short_explanation")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError("Judgment field 'short_explanation' must be a non-empty string.")

    return AnswerJudgment(
        correctness=scores["correctness"],
        relevance=scores["relevance"],
        clarity=scores["clarity"],
        pedagogical_usefulness=scores["pedagogical_usefulness"],
        faithfulness_to_chunks=scores["faithfulness_to_chunks"],
        overall=scores["overall"],
        short_explanation=explanation.strip(),
    )


def _loads_json_object(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        payload = json.loads(cleaned[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("Judgment response must be a JSON object.")
    return payload


def write_judgments_jsonl(judgments: list[JudgmentRecord], path: Path) -> None:
    """Write blinded answer judgments as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for judgment in judgments:
            payload = {
                "query_id": judgment.query_id,
                "question": judgment.question,
                "method_label": judgment.method_label,
                "judge_model": judgment.judge_model,
                "judgment": asdict(judgment.judgment),
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def summarize_by_method(
    judgments: list[JudgmentRecord],
    key: dict[tuple[str, str], str],
) -> list[MethodJudgmentSummary]:
    """Aggregate average judgment scores by actual retrieval method."""
    grouped: dict[str, list[AnswerJudgment]] = {}
    for judgment in judgments:
        actual_method = key.get((judgment.query_id, judgment.method_label))
        if actual_method is None:
            raise ValueError(
                f"No key mapping for query_id={judgment.query_id!r}, "
                f"method_label={judgment.method_label!r}."
            )
        grouped.setdefault(actual_method, []).append(judgment.judgment)

    summaries: list[MethodJudgmentSummary] = []
    for method in sorted(grouped):
        rows = grouped[method]
        summaries.append(
            MethodJudgmentSummary(
                method=method,
                count=len(rows),
                correctness=_mean_score(rows, "correctness"),
                relevance=_mean_score(rows, "relevance"),
                clarity=_mean_score(rows, "clarity"),
                pedagogical_usefulness=_mean_score(rows, "pedagogical_usefulness"),
                faithfulness_to_chunks=_mean_score(rows, "faithfulness_to_chunks"),
                overall=_mean_score(rows, "overall"),
            )
        )
    return summaries


def _mean_score(rows: list[AnswerJudgment], field: str) -> float:
    return statistics.fmean(getattr(row, field) for row in rows)


def write_summary_csv(summaries: list[MethodJudgmentSummary], path: Path) -> None:
    """Write method-level summary CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "method",
                "count",
                "correctness",
                "relevance",
                "clarity",
                "pedagogical_usefulness",
                "faithfulness_to_chunks",
                "overall",
            ],
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "method": summary.method,
                    "count": summary.count,
                    "correctness": f"{summary.correctness:.3f}",
                    "relevance": f"{summary.relevance:.3f}",
                    "clarity": f"{summary.clarity:.3f}",
                    "pedagogical_usefulness": f"{summary.pedagogical_usefulness:.3f}",
                    "faithfulness_to_chunks": f"{summary.faithfulness_to_chunks:.3f}",
                    "overall": f"{summary.overall:.3f}",
                }
            )


def write_report(
    summaries: list[MethodJudgmentSummary],
    judgments: list[JudgmentRecord],
    path: Path,
) -> None:
    """Write a Markdown answer judgment report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Answer Judgment Report",
        "",
        f"Judged answers: {len(judgments)}",
        "",
        "Raw judgments are blinded by method label. This report summarizes scores after joining with the review key.",
        "",
        "## Mean Scores By Method",
        "",
        "| Method | n | Correctness | Relevance | Clarity | Pedagogical usefulness | Faithfulness | Overall |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    summary.method,
                    str(summary.count),
                    f"{summary.correctness:.2f}",
                    f"{summary.relevance:.2f}",
                    f"{summary.clarity:.2f}",
                    f"{summary.pedagogical_usefulness:.2f}",
                    f"{summary.faithfulness_to_chunks:.2f}",
                    f"{summary.overall:.2f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Rubric",
            "",
            "- Scores range from 1 to 5.",
            "- `faithfulness_to_chunks` measures support from the retrieved chunks, not external truth.",
            "- Treat these scores as LLM-assisted proxy judgments, not human-grounded labels.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _resolve_judge_model_name() -> str:
    from src.config import get_settings

    settings = get_settings()
    if settings.model_provider == "openai":
        return settings.openai_llm_model
    if settings.model_provider == "anthropic":
        return settings.anthropic_llm_model
    if settings.model_provider == "local":
        return settings.local_llm_model
    return settings.model_provider


def resolve_paths(
    *,
    run_dir: Path | None,
    records: Path | None,
    key: Path | None,
    judgments_output: Path | None,
    summary_output: Path | None,
    report_output: Path | None,
) -> tuple[Path, Path, Path, Path, Path]:
    """Resolve input/output paths from a run directory or explicit files."""
    if run_dir is not None:
        return (
            records or run_dir / "review_records.jsonl",
            key or run_dir / "review_key.csv",
            judgments_output or run_dir / "answer_judgments.jsonl",
            summary_output or run_dir / "answer_judgment_summary.csv",
            report_output or run_dir / "answer_judgment_report.md",
        )
    return (
        records or Path("data/retrieval_review/review_records.jsonl"),
        key or Path("data/retrieval_review/review_key.csv"),
        judgments_output or Path("data/retrieval_review/answer_judgments.jsonl"),
        summary_output or Path("data/retrieval_review/answer_judgment_summary.csv"),
        report_output or Path("data/retrieval_review/answer_judgment_report.md"),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge anonymized RAG answers with the configured project LLM."
    )
    parser.add_argument("--run-dir", type=Path, default=None, help="Review run directory.")
    parser.add_argument("--records", type=Path, default=None, help="review_records.jsonl path.")
    parser.add_argument("--key", type=Path, default=None, help="review_key.csv path.")
    parser.add_argument(
        "--judgments-output",
        type=Path,
        default=None,
        help="answer_judgments.jsonl output path.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=None,
        help="answer_judgment_summary.csv output path.",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=None,
        help="answer_judgment_report.md output path.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Judge only the first N records.")
    parser.add_argument(
        "--max-chunk-chars",
        type=int,
        default=1800,
        help="Maximum characters per chunk included in the judge prompt. Use 0 for no truncation.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Write a low-score placeholder if a judgment call fails.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    records_path, key_path, judgments_path, summary_path, report_path = resolve_paths(
        run_dir=args.run_dir,
        records=args.records,
        key=args.key,
        judgments_output=args.judgments_output,
        summary_output=args.summary_output,
        report_output=args.report_output,
    )
    answers = load_review_answers(records_path, limit=args.limit)
    judgments = judge_answers(
        answers,
        max_chunk_chars=args.max_chunk_chars,
        continue_on_error=args.continue_on_error,
    )
    key = load_review_key(key_path)
    summaries = summarize_by_method(judgments, key)

    write_judgments_jsonl(judgments, judgments_path)
    write_summary_csv(summaries, summary_path)
    write_report(summaries, judgments, report_path)

    print(f"Wrote answer judgments to {judgments_path}")
    print(f"Wrote answer judgment summary to {summary_path}")
    print(f"Wrote answer judgment report to {report_path}")


if __name__ == "__main__":
    main()
