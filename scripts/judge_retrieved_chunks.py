"""Judge retrieved chunk relevance with the configured project LLM.

Usage:
    python -m scripts.judge_retrieved_chunks \
        --run-dir data/retrieval_review/run_20260510_120000 \
        --limit-records 3

The raw judgment JSONL stays blinded: it contains the anonymized method label,
not the actual retrieval method. Summary files join with ``review_key.csv``.
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
from typing import Any, Literal

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

ChunkLabel = Literal[
    "direct_relevance",
    "support_relevance",
    "marginal",
    "irrelevant",
    "redundant",
]

_VALID_LABELS: set[str] = {
    "direct_relevance",
    "support_relevance",
    "marginal",
    "irrelevant",
    "redundant",
}


@dataclass(frozen=True, slots=True)
class ChunkJudgment:
    label: ChunkLabel
    usefulness_score: int
    include_in_final_prompt: bool
    short_explanation: str


@dataclass(frozen=True, slots=True)
class ChunkJudgmentRecord:
    query_id: str
    question: str
    method_label: str
    chunk_rank: int
    chunk_id: str
    source: str
    page: str
    judgment: ChunkJudgment
    judge_model: str


@dataclass(frozen=True, slots=True)
class ChunkJudgmentSummary:
    method: str
    count: int
    direct_relevance: int
    support_relevance: int
    marginal: int
    irrelevant: int
    redundant: int
    useful_rate: float
    include_rate: float
    mean_usefulness_score: float


def load_review_records(path: Path, *, limit_records: int | None = None) -> list[dict[str, Any]]:
    """Load anonymized review records."""
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                records.append(payload)
            if limit_records is not None and len(records) >= limit_records:
                break
    return records


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


def judge_chunks(
    review_records: list[dict[str, Any]],
    *,
    max_chunk_chars: int,
    limit_chunks: int | None,
    continue_on_error: bool,
) -> list[ChunkJudgmentRecord]:
    """Judge every chunk in the supplied review records."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    from src.models import get_llm

    judge_model = _resolve_judge_model_name()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a careful evaluator for a bachelor thesis RAG experiment. "
                "Judge one retrieved chunk at a time for usefulness to answering the "
                "question. Return only valid JSON with exactly these keys: label, "
                "usefulness_score, include_in_final_prompt, short_explanation.",
            ),
            (
                "human",
                "Question:\n{question}\n\nChunk under review:\n{chunk}\n\n"
                "Other retrieved chunk IDs for the same answer:\n{other_chunk_ids}\n\n"
                "Rubric labels:\n"
                "- direct_relevance: contains information that directly answers the question.\n"
                "- support_relevance: provides useful conceptual, definitional, or contextual support.\n"
                "- marginal: somewhat related but not useful enough to justify prompt budget.\n"
                "- irrelevant: not meaningfully useful for answering the question.\n"
                "- redundant: largely duplicates another retrieved chunk without adding useful information.\n\n"
                "Return JSON only. usefulness_score must be an integer from 0 to 3. "
                "include_in_final_prompt must be true or false.",
            ),
        ]
    )
    chain = prompt | get_llm(temperature=0.0) | StrOutputParser()

    judgments: list[ChunkJudgmentRecord] = []
    for record in review_records:
        query_id = str(record.get("query_id", "")).strip()
        question = str(record.get("question", "")).strip()
        method_label = str(record.get("method_label", "")).strip()
        chunks = [chunk for chunk in record.get("chunks", []) if isinstance(chunk, dict)]
        if limit_chunks is not None:
            chunks = chunks[:limit_chunks]
        other_ids = [
            str(chunk.get("chunk_id", "")).strip()
            for chunk in chunks
            if str(chunk.get("chunk_id", "")).strip()
        ]

        for chunk in chunks:
            chunk_rank = int(chunk.get("rank", 0) or 0)
            chunk_id = str(chunk.get("chunk_id", "")).strip()
            print(f"Judging chunk {query_id} {method_label} rank {chunk_rank}...", flush=True)
            try:
                raw_judgment = chain.invoke(
                    {
                        "question": question,
                        "chunk": format_chunk_for_prompt(chunk, max_chunk_chars=max_chunk_chars),
                        "other_chunk_ids": ", ".join(cid for cid in other_ids if cid != chunk_id),
                    }
                )
                judgment = parse_chunk_judgment_response(raw_judgment)
            except Exception:
                if not continue_on_error:
                    raise
                judgment = ChunkJudgment(
                    label="irrelevant",
                    usefulness_score=0,
                    include_in_final_prompt=False,
                    short_explanation="[Chunk judging failed]",
                )

            judgments.append(
                ChunkJudgmentRecord(
                    query_id=query_id,
                    question=question,
                    method_label=method_label,
                    chunk_rank=chunk_rank,
                    chunk_id=chunk_id,
                    source=str(chunk.get("source", "")).strip(),
                    page=str(chunk.get("page", "")).strip(),
                    judgment=judgment,
                    judge_model=judge_model,
                )
            )
    return judgments


def format_chunk_for_prompt(chunk: dict[str, Any], *, max_chunk_chars: int) -> str:
    """Format one retrieved chunk for an LLM judge prompt."""
    text = str(chunk.get("text", "")).strip()
    if max_chunk_chars > 0 and len(text) > max_chunk_chars:
        text = text[:max_chunk_chars].rstrip() + "\n[truncated]"
    return "\n".join(
        [
            f"chunk_id: {chunk.get('chunk_id', '')}",
            f"source: {chunk.get('source', '')}",
            f"page: {chunk.get('page', '')}",
            text,
        ]
    )


def parse_chunk_judgment_response(raw_response: str) -> ChunkJudgment:
    """Parse and validate a chunk judgment JSON response."""
    payload = _loads_json_object(raw_response)
    label = payload.get("label")
    if label not in _VALID_LABELS:
        raise ValueError(f"Invalid chunk relevance label: {label!r}")
    usefulness_score = payload.get("usefulness_score")
    if not isinstance(usefulness_score, int) or not 0 <= usefulness_score <= 3:
        raise ValueError("usefulness_score must be an integer from 0 to 3.")
    include = payload.get("include_in_final_prompt")
    if not isinstance(include, bool):
        raise ValueError("include_in_final_prompt must be a boolean.")
    explanation = payload.get("short_explanation")
    if not isinstance(explanation, str) or not explanation.strip():
        raise ValueError("short_explanation must be a non-empty string.")
    return ChunkJudgment(
        label=label,  # type: ignore[arg-type]
        usefulness_score=usefulness_score,
        include_in_final_prompt=include,
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
        raise ValueError("Chunk judgment response must be a JSON object.")
    return payload


def write_chunk_judgments_jsonl(judgments: list[ChunkJudgmentRecord], path: Path) -> None:
    """Write blinded chunk judgments as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for judgment in judgments:
            payload = {
                "query_id": judgment.query_id,
                "question": judgment.question,
                "method_label": judgment.method_label,
                "chunk_rank": judgment.chunk_rank,
                "chunk_id": judgment.chunk_id,
                "source": judgment.source,
                "page": judgment.page,
                "judge_model": judgment.judge_model,
                "judgment": asdict(judgment.judgment),
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def summarize_by_method(
    judgments: list[ChunkJudgmentRecord],
    key: dict[tuple[str, str], str],
) -> list[ChunkJudgmentSummary]:
    """Aggregate chunk relevance judgments by actual method."""
    grouped: dict[str, list[ChunkJudgment]] = {}
    for judgment in judgments:
        actual_method = key.get((judgment.query_id, judgment.method_label))
        if actual_method is None:
            raise ValueError(
                f"No key mapping for query_id={judgment.query_id!r}, "
                f"method_label={judgment.method_label!r}."
            )
        grouped.setdefault(actual_method, []).append(judgment.judgment)

    summaries: list[ChunkJudgmentSummary] = []
    for method in sorted(grouped):
        rows = grouped[method]
        label_counts = {label: sum(row.label == label for row in rows) for label in _VALID_LABELS}
        useful_count = label_counts["direct_relevance"] + label_counts["support_relevance"]
        summaries.append(
            ChunkJudgmentSummary(
                method=method,
                count=len(rows),
                direct_relevance=label_counts["direct_relevance"],
                support_relevance=label_counts["support_relevance"],
                marginal=label_counts["marginal"],
                irrelevant=label_counts["irrelevant"],
                redundant=label_counts["redundant"],
                useful_rate=useful_count / len(rows) if rows else 0.0,
                include_rate=sum(row.include_in_final_prompt for row in rows) / len(rows)
                if rows
                else 0.0,
                mean_usefulness_score=statistics.fmean(row.usefulness_score for row in rows)
                if rows
                else 0.0,
            )
        )
    return summaries


def write_summary_csv(summaries: list[ChunkJudgmentSummary], path: Path) -> None:
    """Write method-level chunk relevance summary CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(summaries[0]).keys()) if summaries else [])
        if summaries:
            writer.writeheader()
            for summary in summaries:
                writer.writerow(asdict(summary))


def write_report(
    summaries: list[ChunkJudgmentSummary],
    judgments: list[ChunkJudgmentRecord],
    path: Path,
) -> None:
    """Write a Markdown chunk relevance report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Chunk Relevance Judgment Report",
        "",
        f"Judged chunks: {len(judgments)}",
        "",
        "Raw chunk judgments are blinded by method label. This report summarizes scores after joining with the review key.",
        "",
        "| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    summary.method,
                    str(summary.count),
                    str(summary.direct_relevance),
                    str(summary.support_relevance),
                    str(summary.marginal),
                    str(summary.irrelevant),
                    str(summary.redundant),
                    f"{summary.useful_rate:.1%}",
                    f"{summary.include_rate:.1%}",
                    f"{summary.mean_usefulness_score:.2f}",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Useful chunks are `direct_relevance` plus `support_relevance`.",
            "Treat these labels as LLM-assisted proxy judgments unless manually validated.",
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
            judgments_output or run_dir / "chunk_judgments.jsonl",
            summary_output or run_dir / "chunk_judgment_summary.csv",
            report_output or run_dir / "chunk_judgment_report.md",
        )
    return (
        records or Path("data/retrieval_review/review_records.jsonl"),
        key or Path("data/retrieval_review/review_key.csv"),
        judgments_output or Path("data/retrieval_review/chunk_judgments.jsonl"),
        summary_output or Path("data/retrieval_review/chunk_judgment_summary.csv"),
        report_output or Path("data/retrieval_review/chunk_judgment_report.md"),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge retrieved chunk relevance with the configured project LLM."
    )
    parser.add_argument("--run-dir", type=Path, default=None, help="Review run directory.")
    parser.add_argument("--records", type=Path, default=None, help="review_records.jsonl path.")
    parser.add_argument("--key", type=Path, default=None, help="review_key.csv path.")
    parser.add_argument("--judgments-output", type=Path, default=None)
    parser.add_argument("--summary-output", type=Path, default=None)
    parser.add_argument("--report-output", type=Path, default=None)
    parser.add_argument("--limit-records", type=int, default=None)
    parser.add_argument("--limit-chunks", type=int, default=None)
    parser.add_argument("--max-chunk-chars", type=int, default=1800)
    parser.add_argument("--continue-on-error", action="store_true")
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
    records = load_review_records(records_path, limit_records=args.limit_records)
    judgments = judge_chunks(
        records,
        max_chunk_chars=args.max_chunk_chars,
        limit_chunks=args.limit_chunks,
        continue_on_error=args.continue_on_error,
    )
    key = load_review_key(key_path)
    summaries = summarize_by_method(judgments, key)
    write_chunk_judgments_jsonl(judgments, judgments_path)
    write_summary_csv(summaries, summary_path)
    write_report(summaries, judgments, report_path)

    print(f"Wrote chunk judgments to {judgments_path}")
    print(f"Wrote chunk judgment summary to {summary_path}")
    print(f"Wrote chunk judgment report to {report_path}")


if __name__ == "__main__":
    main()
