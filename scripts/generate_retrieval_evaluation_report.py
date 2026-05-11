"""Generate a combined thesis-friendly report for anonymized RAG evaluations.

Usage:
    python -m scripts.generate_retrieval_evaluation_report \
        --run-dir data/retrieval_review/run_20260510_155212

The script joins anonymized review outputs with ``review_key.csv`` only for
aggregate reporting. Raw answer and chunk judgment files can remain blinded.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RUBRIC_FIELDS = [
    "correctness",
    "relevance",
    "clarity",
    "pedagogical_usefulness",
    "faithfulness_to_chunks",
    "overall",
]

CHUNK_LABELS = [
    "direct_relevance",
    "support_relevance",
    "marginal",
    "irrelevant",
    "redundant",
]


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    query_id: str
    question: str
    method_label: str
    method: str
    answer: str
    retrieval_latency_seconds: float
    generation_latency_seconds: float
    chunk_ids: tuple[str, ...]
    source_documents: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnswerJudgmentRecord:
    query_id: str
    method_label: str
    method: str
    scores: dict[str, int]


@dataclass(frozen=True, slots=True)
class ChunkJudgmentRecord:
    query_id: str
    method_label: str
    method: str
    label: str
    usefulness_score: int
    include_in_final_prompt: bool


@dataclass(frozen=True, slots=True)
class AnswerSummary:
    method: str
    count: int
    means: dict[str, float]
    overall_ci_low: float
    overall_ci_high: float


@dataclass(frozen=True, slots=True)
class ChunkSummary:
    method: str
    count: int
    label_counts: dict[str, int]
    useful_rate: float
    include_rate: float
    mean_usefulness_score: float


def load_review_key(path: Path) -> dict[tuple[str, str], str]:
    """Load the method-label key produced with the anonymized review package."""
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


def load_review_records(path: Path, key: dict[tuple[str, str], str]) -> list[ReviewRecord]:
    """Load anonymized review records and attach actual methods for aggregate analysis."""
    records: list[ReviewRecord] = []
    for line_number, payload in _iter_jsonl(path):
        query_id = _required_string(payload, "query_id", line_number)
        method_label = _required_string(payload, "method_label", line_number)
        method = _lookup_method(key, query_id, method_label)
        chunks = [chunk for chunk in payload.get("chunks", []) if isinstance(chunk, dict)]
        chunk_ids = tuple(
            str(chunk.get("chunk_id", "")).strip()
            for chunk in chunks
            if str(chunk.get("chunk_id", "")).strip()
        )
        source_documents = tuple(
            sorted(
                {
                    str(chunk.get("document_id") or chunk.get("source") or "").strip()
                    for chunk in chunks
                    if str(chunk.get("document_id") or chunk.get("source") or "").strip()
                }
            )
        )
        records.append(
            ReviewRecord(
                query_id=query_id,
                question=_required_string(payload, "question", line_number),
                method_label=method_label,
                method=method,
                answer=_required_string(payload, "answer", line_number),
                retrieval_latency_seconds=_optional_float(payload, "retrieval_latency_seconds"),
                generation_latency_seconds=_optional_float(payload, "generation_latency_seconds"),
                chunk_ids=chunk_ids,
                source_documents=source_documents,
            )
        )
    return records


def load_answer_judgments(
    path: Path,
    key: dict[tuple[str, str], str],
) -> list[AnswerJudgmentRecord]:
    """Load blinded answer judgments and attach actual methods for aggregate analysis."""
    if not path.exists():
        return []
    records: list[AnswerJudgmentRecord] = []
    for line_number, payload in _iter_jsonl(path):
        query_id = _required_string(payload, "query_id", line_number)
        method_label = _required_string(payload, "method_label", line_number)
        judgment = payload.get("judgment")
        if not isinstance(judgment, dict):
            raise ValueError(f"Line {line_number} is missing object field 'judgment'.")
        scores = {
            field: _required_score(judgment, field, line_number)
            for field in RUBRIC_FIELDS
        }
        records.append(
            AnswerJudgmentRecord(
                query_id=query_id,
                method_label=method_label,
                method=_lookup_method(key, query_id, method_label),
                scores=scores,
            )
        )
    return records


def load_chunk_judgments(
    path: Path,
    key: dict[tuple[str, str], str],
) -> list[ChunkJudgmentRecord]:
    """Load blinded chunk judgments and attach actual methods for aggregate analysis."""
    if not path.exists():
        return []
    records: list[ChunkJudgmentRecord] = []
    for line_number, payload in _iter_jsonl(path):
        query_id = _required_string(payload, "query_id", line_number)
        method_label = _required_string(payload, "method_label", line_number)
        judgment = payload.get("judgment")
        if not isinstance(judgment, dict):
            raise ValueError(f"Line {line_number} is missing object field 'judgment'.")
        label = str(judgment.get("label", "")).strip()
        if label not in CHUNK_LABELS:
            raise ValueError(f"Line {line_number} has invalid chunk judgment label {label!r}.")
        usefulness_score = judgment.get("usefulness_score")
        if not isinstance(usefulness_score, int):
            raise ValueError(f"Line {line_number} is missing integer usefulness_score.")
        include = judgment.get("include_in_final_prompt")
        if not isinstance(include, bool):
            raise ValueError(f"Line {line_number} is missing boolean include_in_final_prompt.")
        records.append(
            ChunkJudgmentRecord(
                query_id=query_id,
                method_label=method_label,
                method=_lookup_method(key, query_id, method_label),
                label=label,
                usefulness_score=usefulness_score,
                include_in_final_prompt=include,
            )
        )
    return records


def load_speed_summaries(path: Path) -> list[dict[str, Any]]:
    """Load retrieval speed summary JSON if it exists."""
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list.")
    return [row for row in payload if isinstance(row, dict)]


def load_query_topics(path: Path | None) -> dict[str, str]:
    """Load optional query metadata topics from the original JSON query file."""
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list of queries.")
    topics: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        query_id = str(item.get("id", "")).strip()
        metadata = item.get("metadata")
        topic = ""
        if isinstance(metadata, dict):
            topic = str(metadata.get("topic", "")).strip()
        if query_id and topic:
            topics[query_id] = topic
    return topics


def summarize_answers(
    records: list[AnswerJudgmentRecord],
    *,
    bootstrap_samples: int,
    seed: int,
) -> list[AnswerSummary]:
    """Summarize LLM answer-judgment scores by retrieval method."""
    summaries: list[AnswerSummary] = []
    for method in sorted({record.method for record in records}):
        method_records = [record for record in records if record.method == method]
        means = {
            field: statistics.fmean(record.scores[field] for record in method_records)
            for field in RUBRIC_FIELDS
        }
        low, high = bootstrap_mean_ci(
            [record.scores["overall"] for record in method_records],
            samples=bootstrap_samples,
            seed=seed,
        )
        summaries.append(
            AnswerSummary(
                method=method,
                count=len(method_records),
                means=means,
                overall_ci_low=low,
                overall_ci_high=high,
            )
        )
    return summaries


def summarize_chunks(records: list[ChunkJudgmentRecord]) -> list[ChunkSummary]:
    """Summarize LLM chunk-judgment labels by retrieval method."""
    summaries: list[ChunkSummary] = []
    for method in sorted({record.method for record in records}):
        method_records = [record for record in records if record.method == method]
        label_counts = {
            label: sum(record.label == label for record in method_records)
            for label in CHUNK_LABELS
        }
        useful_count = label_counts["direct_relevance"] + label_counts["support_relevance"]
        summaries.append(
            ChunkSummary(
                method=method,
                count=len(method_records),
                label_counts=label_counts,
                useful_rate=useful_count / len(method_records) if method_records else 0.0,
                include_rate=sum(record.include_in_final_prompt for record in method_records)
                / len(method_records)
                if method_records
                else 0.0,
                mean_usefulness_score=statistics.fmean(
                    record.usefulness_score for record in method_records
                )
                if method_records
                else 0.0,
            )
        )
    return summaries


def bootstrap_mean_ci(
    values: list[int | float],
    *,
    samples: int,
    seed: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Return a bootstrap percentile confidence interval for the mean."""
    if not values:
        return (0.0, 0.0)
    if len(values) == 1 or samples <= 0:
        value = float(statistics.fmean(values))
        return (value, value)

    rng = random.Random(seed)
    simulated_means: list[float] = []
    n = len(values)
    for _ in range(samples):
        simulated_means.append(statistics.fmean(rng.choice(values) for _ in range(n)))

    simulated_means.sort()
    tail = (1.0 - confidence) / 2.0
    low_index = min(max(round(tail * (samples - 1)), 0), samples - 1)
    high_index = min(max(round((1.0 - tail) * (samples - 1)), 0), samples - 1)
    return (simulated_means[low_index], simulated_means[high_index])


def compute_winner_counts(records: list[AnswerJudgmentRecord]) -> dict[str, int]:
    """Count per-question winners by highest average overall score."""
    averaged = _average_answer_scores_by_query_method(records)
    grouped: dict[str, list[tuple[str, float]]] = {}
    for (query_id, method), scores in averaged.items():
        grouped.setdefault(query_id, []).append((method, scores["overall"]))

    winners: dict[str, int] = {}
    for rows in grouped.values():
        if not rows:
            continue
        best_score = max(score for _, score in rows)
        best_methods = [method for method, score in rows if score == best_score]
        winner = best_methods[0] if len(best_methods) == 1 else "tie"
        winners[winner] = winners.get(winner, 0) + 1
    return dict(sorted(winners.items()))


def compute_topic_answer_summary(
    records: list[AnswerJudgmentRecord],
    topics: dict[str, str],
) -> dict[tuple[str, str], tuple[int, float]]:
    """Compute optional mean overall answer score by topic and method."""
    averaged = _average_answer_scores_by_query_method(records)
    grouped: dict[tuple[str, str], list[float]] = {}
    for (query_id, method), scores in averaged.items():
        topic = topics.get(query_id)
        if topic is None:
            continue
        grouped.setdefault((topic, method), []).append(scores["overall"])
    return {
        key: (len(values), statistics.fmean(values))
        for key, values in sorted(grouped.items())
    }


def compute_overlap_matrix(records: list[ReviewRecord]) -> dict[tuple[str, str], float]:
    """Compute average per-query chunk-set Jaccard overlap between methods."""
    by_query: dict[str, dict[str, set[str]]] = {}
    for record in records:
        by_query.setdefault(record.query_id, {})[record.method] = set(record.chunk_ids)

    methods = sorted({record.method for record in records})
    matrix: dict[tuple[str, str], float] = {}
    for left in methods:
        for right in methods:
            scores: list[float] = []
            for method_sets in by_query.values():
                if left not in method_sets or right not in method_sets:
                    continue
                scores.append(jaccard(method_sets[left], method_sets[right]))
            matrix[(left, right)] = statistics.fmean(scores) if scores else 0.0
    return matrix


def summarize_review_records(records: list[ReviewRecord]) -> list[dict[str, Any]]:
    """Summarize retrieved context size and source diversity by method."""
    summaries: list[dict[str, Any]] = []
    for method in sorted({record.method for record in records}):
        method_records = [record for record in records if record.method == method]
        summaries.append(
            {
                "method": method,
                "count": len(method_records),
                "mean_chunks": statistics.fmean(len(record.chunk_ids) for record in method_records),
                "mean_unique_sources": statistics.fmean(
                    len(record.source_documents) for record in method_records
                ),
                "mean_answer_chars": statistics.fmean(len(record.answer) for record in method_records),
            }
        )
    return summaries


def jaccard(left: set[str], right: set[str]) -> float:
    """Return Jaccard similarity for two sets."""
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def write_metrics_summary(
    *,
    answer_summaries: list[AnswerSummary],
    chunk_summaries: list[ChunkSummary],
    winner_counts: dict[str, int],
    overlap_matrix: dict[tuple[str, str], float],
    review_summaries: list[dict[str, Any]],
    speed_summaries: list[dict[str, Any]],
    path: Path,
) -> None:
    """Write machine-readable aggregate metrics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "answer_summaries": [
            {
                "method": summary.method,
                "count": summary.count,
                **{field: summary.means[field] for field in RUBRIC_FIELDS},
                "overall_ci_low": summary.overall_ci_low,
                "overall_ci_high": summary.overall_ci_high,
            }
            for summary in answer_summaries
        ],
        "chunk_summaries": [
            {
                "method": summary.method,
                "count": summary.count,
                **summary.label_counts,
                "useful_rate": summary.useful_rate,
                "include_rate": summary.include_rate,
                "mean_usefulness_score": summary.mean_usefulness_score,
            }
            for summary in chunk_summaries
        ],
        "winner_counts": winner_counts,
        "overlap_matrix": {
            f"{left}__{right}": value
            for (left, right), value in sorted(overlap_matrix.items())
        },
        "review_summaries": review_summaries,
        "speed_summaries": speed_summaries,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_metrics_csv(answer_summaries: list[AnswerSummary], path: Path) -> None:
    """Write a compact answer-score summary CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["method", "count", *RUBRIC_FIELDS, "overall_ci_low", "overall_ci_high"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in answer_summaries:
            writer.writerow(
                {
                    "method": summary.method,
                    "count": summary.count,
                    **{field: f"{summary.means[field]:.3f}" for field in RUBRIC_FIELDS},
                    "overall_ci_low": f"{summary.overall_ci_low:.3f}",
                    "overall_ci_high": f"{summary.overall_ci_high:.3f}",
                }
            )


def write_report(
    *,
    review_records: list[ReviewRecord],
    answer_summaries: list[AnswerSummary],
    chunk_summaries: list[ChunkSummary],
    winner_counts: dict[str, int],
    overlap_matrix: dict[tuple[str, str], float],
    review_summaries: list[dict[str, Any]],
    speed_summaries: list[dict[str, Any]],
    topic_summary: dict[tuple[str, str], tuple[int, float]],
    figure_paths: list[Path],
    path: Path,
) -> None:
    """Write the combined Markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    methods = sorted({record.method for record in review_records})
    lines = [
        "# Retrieval Evaluation Report",
        "",
        f"Queries: {len({record.query_id for record in review_records})}",
        f"Methods: {', '.join(f'`{method}`' for method in methods)}",
        f"Review records: {len(review_records)}",
        "",
        "This report joins anonymized records with `review_key.csv` for aggregate analysis. "
        "LLM-based judgments should be treated as proxy evidence unless manually validated.",
        "",
    ]

    if figure_paths:
        lines.extend(["## Figures", ""])
        for figure_path in figure_paths:
            lines.append(f"- [{figure_path.name}]({figure_path.as_posix()})")
        lines.append("")

    lines.extend(
        [
            "## Answer Judgment Summary",
            "",
            "| Method | n | Correctness | Relevance | Clarity | Pedagogical | Faithfulness | Overall | 95% bootstrap CI |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    if answer_summaries:
        for summary in answer_summaries:
            lines.append(
                "| "
                + " | ".join(
                    [
                        summary.method,
                        str(summary.count),
                        f"{summary.means['correctness']:.2f}",
                        f"{summary.means['relevance']:.2f}",
                        f"{summary.means['clarity']:.2f}",
                        f"{summary.means['pedagogical_usefulness']:.2f}",
                        f"{summary.means['faithfulness_to_chunks']:.2f}",
                        f"{summary.means['overall']:.2f}",
                        f"{summary.overall_ci_low:.2f}-{summary.overall_ci_high:.2f}",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| No answer judgments found |  |  |  |  |  |  |  |  |")

    lines.extend(["", "## Per-Question Winner Counts", "", "| Winner | Count |", "|---|---:|"])
    if winner_counts:
        for winner, count in winner_counts.items():
            lines.append(f"| {winner} | {count} |")
    else:
        lines.append("| No answer judgments found | 0 |")

    lines.extend(
        [
            "",
            "## Chunk Relevance Summary",
            "",
            "| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    if chunk_summaries:
        for summary in chunk_summaries:
            lines.append(
                "| "
                + " | ".join(
                    [
                        summary.method,
                        str(summary.count),
                        str(summary.label_counts["direct_relevance"]),
                        str(summary.label_counts["support_relevance"]),
                        str(summary.label_counts["marginal"]),
                        str(summary.label_counts["irrelevant"]),
                        str(summary.label_counts["redundant"]),
                        f"{summary.useful_rate:.1%}",
                        f"{summary.include_rate:.1%}",
                        f"{summary.mean_usefulness_score:.2f}",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| No chunk judgments found |  |  |  |  |  |  |  |  |  |")

    lines.extend(
        [
            "",
            "## Retrieval Context Summary",
            "",
            "| Method | n | Mean chunks | Mean unique sources | Mean answer characters |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for summary in review_summaries:
        lines.append(
            f"| {summary['method']} | {summary['count']} | "
            f"{summary['mean_chunks']:.2f} | {summary['mean_unique_sources']:.2f} | "
            f"{summary['mean_answer_chars']:.0f} |"
        )

    lines.extend(["", "## Retrieval Speed", "", _speed_table(speed_summaries)])

    lines.extend(
        [
            "",
            "## Retrieved Chunk Overlap",
            "",
            "Average per-query Jaccard similarity between final retrieved chunk sets.",
            "",
            _overlap_table(methods, overlap_matrix),
        ]
    )

    if topic_summary:
        lines.extend(
            [
                "",
                "## Topic Breakdown",
                "",
                "| Topic | Method | n | Mean overall answer score |",
                "|---|---|---:|---:|",
            ]
        )
        for (topic, method), (count, mean_overall) in topic_summary.items():
            lines.append(f"| {topic} | {method} | {count} | {mean_overall:.2f} |")

    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- Normalized final context size helps prevent one method from winning by sending more chunks.",
            "- Chunk judgments expose whether a method retrieves useful context before answer quality is considered.",
            "- Overlap helps show whether methods are genuinely retrieving different evidence.",
            "- Bootstrap intervals are descriptive and depend on the available judged examples.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figures(
    *,
    answer_summaries: list[AnswerSummary],
    chunk_summaries: list[ChunkSummary],
    winner_counts: dict[str, int],
    speed_summaries: list[dict[str, Any]],
    overlap_matrix: dict[tuple[str, str], float],
    output_dir: Path,
) -> list[Path]:
    """Write simple SVG charts that can be included in thesis drafts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if answer_summaries:
        path = output_dir / "answer_overall_scores.svg"
        write_bar_chart(
            path,
            title="Mean Overall Answer Score",
            values={summary.method: summary.means["overall"] for summary in answer_summaries},
            max_value=5.0,
            value_suffix="",
        )
        written.append(path)

        path = output_dir / "answer_rubric_scores.svg"
        write_grouped_bar_chart(
            path,
            title="Mean Answer Rubric Scores",
            groups=[summary.method for summary in answer_summaries],
            series={
                field: [summary.means[field] for summary in answer_summaries]
                for field in RUBRIC_FIELDS
            },
            max_value=5.0,
        )
        written.append(path)

    if winner_counts:
        path = output_dir / "answer_winner_counts.svg"
        write_bar_chart(
            path,
            title="Per-Question Winner Counts",
            values={winner: float(count) for winner, count in winner_counts.items()},
            max_value=max(winner_counts.values()),
            value_suffix="",
        )
        written.append(path)

    if chunk_summaries:
        path = output_dir / "chunk_relevance_distribution.svg"
        write_stacked_bar_chart(
            path,
            title="Chunk Relevance Label Distribution",
            groups=[summary.method for summary in chunk_summaries],
            series={
                label: [summary.label_counts[label] for summary in chunk_summaries]
                for label in CHUNK_LABELS
            },
        )
        written.append(path)

    if speed_summaries:
        path = output_dir / "retrieval_latency_means.svg"
        write_bar_chart(
            path,
            title="Mean Retrieval Latency",
            values={
                str(row.get("method", "")): float(row.get("mean_seconds", 0.0))
                for row in speed_summaries
            },
            max_value=max(float(row.get("mean_seconds", 0.0)) for row in speed_summaries),
            value_suffix="s",
        )
        written.append(path)

    if overlap_matrix:
        path = output_dir / "retrieval_chunk_overlap.svg"
        write_heatmap(path, title="Retrieved Chunk Overlap", matrix=overlap_matrix)
        written.append(path)

    return written


def write_bar_chart(
    path: Path,
    *,
    title: str,
    values: dict[str, float],
    max_value: float,
    value_suffix: str,
) -> None:
    """Write a compact SVG bar chart."""
    width = 860
    height = 420
    margin_left = 170
    margin_right = 50
    margin_top = 70
    bar_height = 38
    gap = 24
    chart_width = width - margin_left - margin_right
    max_value = max(max_value, 0.001)
    rows: list[str] = [_svg_header(width, height, title)]
    for index, (label, value) in enumerate(values.items()):
        y = margin_top + index * (bar_height + gap)
        bar_width = chart_width * (value / max_value)
        rows.append(f'<text x="20" y="{y + 25}" class="label">{_esc(label)}</text>')
        rows.append(
            f'<rect x="{margin_left}" y="{y}" width="{bar_width:.1f}" '
            f'height="{bar_height}" fill="#2f7d7e" rx="4" />'
        )
        rows.append(
            f'<text x="{margin_left + bar_width + 8:.1f}" y="{y + 25}" class="value">'
            f'{value:.2f}{value_suffix}</text>'
        )
    rows.append(_svg_footer())
    path.write_text("\n".join(rows), encoding="utf-8")


def write_grouped_bar_chart(
    path: Path,
    *,
    title: str,
    groups: list[str],
    series: dict[str, list[float]],
    max_value: float,
) -> None:
    """Write a grouped SVG bar chart."""
    width = 980
    height = 520
    left = 120
    top = 90
    chart_height = 300
    chart_width = 780
    colors = ["#2f7d7e", "#805b9b", "#b35f45", "#526c2d", "#4c6f9f", "#8a6d2c"]
    group_width = chart_width / max(len(groups), 1)
    bar_width = group_width / max(len(series) + 1, 1)
    rows = [_svg_header(width, height, title)]
    for group_index, group in enumerate(groups):
        x0 = left + group_index * group_width
        rows.append(
            f'<text x="{x0 + group_width / 2:.1f}" y="{top + chart_height + 32}" '
            f'class="tick" text-anchor="middle">{_esc(group)}</text>'
        )
        for series_index, (name, values) in enumerate(series.items()):
            value = values[group_index]
            bar_height = chart_height * (value / max_value)
            x = x0 + series_index * bar_width + bar_width * 0.5
            y = top + chart_height - bar_height
            rows.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width * 0.72:.1f}" '
                f'height="{bar_height:.1f}" fill="{colors[series_index % len(colors)]}" />'
            )
    for index, name in enumerate(series):
        x = left + index * 150
        y = height - 60
        rows.append(f'<rect x="{x}" y="{y}" width="14" height="14" fill="{colors[index]}" />')
        rows.append(f'<text x="{x + 22}" y="{y + 12}" class="legend">{_esc(name)}</text>')
    rows.append(_svg_footer())
    path.write_text("\n".join(rows), encoding="utf-8")


def write_stacked_bar_chart(
    path: Path,
    *,
    title: str,
    groups: list[str],
    series: dict[str, list[int]],
) -> None:
    """Write a normalized stacked SVG bar chart."""
    width = 900
    height = 460
    left = 170
    top = 80
    bar_height = 38
    gap = 28
    chart_width = 610
    colors = {
        "direct_relevance": "#2f7d7e",
        "support_relevance": "#526c2d",
        "marginal": "#d29b43",
        "irrelevant": "#b35f45",
        "redundant": "#805b9b",
    }
    rows = [_svg_header(width, height, title)]
    for group_index, group in enumerate(groups):
        y = top + group_index * (bar_height + gap)
        total = sum(values[group_index] for values in series.values()) or 1
        x = left
        rows.append(f'<text x="20" y="{y + 25}" class="label">{_esc(group)}</text>')
        for name, values in series.items():
            width_part = chart_width * values[group_index] / total
            rows.append(
                f'<rect x="{x:.1f}" y="{y}" width="{width_part:.1f}" height="{bar_height}" '
                f'fill="{colors[name]}" />'
            )
            x += width_part
    legend_y = height - 70
    legend_x = 20
    for index, name in enumerate(series):
        x = legend_x + index * 170
        rows.append(f'<rect x="{x}" y="{legend_y}" width="14" height="14" fill="{colors[name]}" />')
        rows.append(f'<text x="{x + 22}" y="{legend_y + 12}" class="legend">{_esc(name)}</text>')
    rows.append(_svg_footer())
    path.write_text("\n".join(rows), encoding="utf-8")


def write_heatmap(path: Path, *, title: str, matrix: dict[tuple[str, str], float]) -> None:
    """Write a simple SVG heatmap for pairwise chunk overlap."""
    methods = sorted({method for pair in matrix for method in pair})
    cell = 90
    left = 170
    top = 80
    width = left + cell * len(methods) + 70
    height = top + cell * len(methods) + 80
    rows = [_svg_header(width, height, title)]
    for col, method in enumerate(methods):
        rows.append(
            f'<text x="{left + col * cell + cell / 2}" y="58" class="tick" '
            f'text-anchor="middle">{_esc(method)}</text>'
        )
    for row, left_method in enumerate(methods):
        rows.append(f'<text x="20" y="{top + row * cell + 52}" class="label">{_esc(left_method)}</text>')
        for col, right_method in enumerate(methods):
            value = matrix.get((left_method, right_method), 0.0)
            intensity = int(240 - value * 150)
            color = f"rgb({intensity},{240 - int(value * 80)},{235 - int(value * 90)})"
            x = left + col * cell
            y = top + row * cell
            rows.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" />')
            rows.append(
                f'<text x="{x + cell / 2}" y="{y + 52}" class="value" text-anchor="middle">'
                f'{value:.2f}</text>'
            )
    rows.append(_svg_footer())
    path.write_text("\n".join(rows), encoding="utf-8")


def resolve_paths(
    *,
    run_dir: Path | None,
    records: Path | None,
    key: Path | None,
    answer_judgments: Path | None,
    chunk_judgments: Path | None,
    speed_summary: Path | None,
    output: Path | None,
    metrics_json: Path | None,
    metrics_csv: Path | None,
    figures_dir: Path | None,
) -> tuple[Path, Path, Path, Path, Path, Path, Path, Path, Path]:
    """Resolve conventional run-directory paths while allowing explicit overrides."""
    base = run_dir or Path("data/retrieval_review")
    return (
        records or base / "review_records.jsonl",
        key or base / "review_key.csv",
        answer_judgments or base / "answer_judgments.jsonl",
        chunk_judgments or base / "chunk_judgments.jsonl",
        speed_summary or base / "retrieval_speed_summary.json",
        output or base / "evaluation_report.md",
        metrics_json or base / "metrics_summary.json",
        metrics_csv or base / "metrics_summary.csv",
        figures_dir or base / "figures",
    )


def generate_report(
    *,
    records_path: Path,
    key_path: Path,
    answer_judgments_path: Path,
    chunk_judgments_path: Path,
    speed_summary_path: Path,
    queries_json_path: Path | None,
    output_path: Path,
    metrics_json_path: Path,
    metrics_csv_path: Path,
    figures_dir: Path,
    bootstrap_samples: int,
    seed: int,
) -> None:
    """Generate all combined report outputs."""
    key = load_review_key(key_path)
    review_records = load_review_records(records_path, key)
    answer_judgments = load_answer_judgments(answer_judgments_path, key)
    chunk_judgments = load_chunk_judgments(chunk_judgments_path, key)
    speed_summaries = load_speed_summaries(speed_summary_path)
    topics = load_query_topics(queries_json_path)

    answer_summaries = summarize_answers(
        answer_judgments,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    chunk_summaries = summarize_chunks(chunk_judgments)
    winner_counts = compute_winner_counts(answer_judgments)
    overlap_matrix = compute_overlap_matrix(review_records)
    review_summaries = summarize_review_records(review_records)
    topic_summary = compute_topic_answer_summary(answer_judgments, topics)
    figure_paths = write_figures(
        answer_summaries=answer_summaries,
        chunk_summaries=chunk_summaries,
        winner_counts=winner_counts,
        speed_summaries=speed_summaries,
        overlap_matrix=overlap_matrix,
        output_dir=figures_dir,
    )

    write_metrics_summary(
        answer_summaries=answer_summaries,
        chunk_summaries=chunk_summaries,
        winner_counts=winner_counts,
        overlap_matrix=overlap_matrix,
        review_summaries=review_summaries,
        speed_summaries=speed_summaries,
        path=metrics_json_path,
    )
    write_metrics_csv(answer_summaries, metrics_csv_path)
    write_report(
        review_records=review_records,
        answer_summaries=answer_summaries,
        chunk_summaries=chunk_summaries,
        winner_counts=winner_counts,
        overlap_matrix=overlap_matrix,
        review_summaries=review_summaries,
        speed_summaries=speed_summaries,
        topic_summary=topic_summary,
        figure_paths=figure_paths,
        path=output_path,
    )


def _average_answer_scores_by_query_method(
    records: list[AnswerJudgmentRecord],
) -> dict[tuple[str, str], dict[str, float]]:
    grouped: dict[tuple[str, str], list[AnswerJudgmentRecord]] = {}
    for record in records:
        grouped.setdefault((record.query_id, record.method), []).append(record)
    return {
        key: {
            field: statistics.fmean(record.scores[field] for record in grouped_records)
            for field in RUBRIC_FIELDS
        }
        for key, grouped_records in grouped.items()
    }


def _iter_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"Line {line_number} in {path} is not a JSON object.")
            rows.append((line_number, payload))
    return rows


def _lookup_method(key: dict[tuple[str, str], str], query_id: str, method_label: str) -> str:
    method = key.get((query_id, method_label))
    if method is None:
        raise ValueError(
            f"No review key entry for query_id={query_id!r}, method_label={method_label!r}."
        )
    return method


def _required_string(payload: dict[str, Any], key: str, line_number: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Line {line_number} is missing non-empty string field {key!r}.")
    return value.strip()


def _optional_float(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key, 0.0)
    return float(value) if isinstance(value, int | float) else 0.0


def _required_score(payload: dict[str, Any], key: str, line_number: int) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Line {line_number} is missing integer score {key!r}.")
    return value


def _speed_table(speed_summaries: list[dict[str, Any]]) -> str:
    if not speed_summaries:
        return "No retrieval speed summary found."
    lines = [
        "| Method | n | Mean | Median | P95 | Max |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in speed_summaries:
        lines.append(
            f"| {row.get('method', '')} | {row.get('count', '')} | "
            f"{float(row.get('mean_seconds', 0.0)):.3f}s | "
            f"{float(row.get('median_seconds', 0.0)):.3f}s | "
            f"{float(row.get('p95_seconds', 0.0)):.3f}s | "
            f"{float(row.get('max_seconds', 0.0)):.3f}s |"
        )
    return "\n".join(lines)


def _overlap_table(methods: list[str], overlap_matrix: dict[tuple[str, str], float]) -> str:
    if not overlap_matrix:
        return "No retrieval overlap data found."
    header = "| Method | " + " | ".join(methods) + " |"
    divider = "|---|" + "|".join("---:" for _ in methods) + "|"
    rows = [header, divider]
    for left in methods:
        values = [
            f"{overlap_matrix.get((left, right), 0.0):.2f}"
            for right in methods
        ]
        rows.append("| " + " | ".join([left, *values]) + " |")
    return "\n".join(rows)


def _svg_header(width: int, height: int, title: str) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">',
            "<style>",
            "text{font-family:Arial,Helvetica,sans-serif;fill:#1f2933}",
            ".title{font-size:22px;font-weight:700}",
            ".label{font-size:14px}",
            ".tick{font-size:12px}",
            ".value{font-size:13px;font-weight:700}",
            ".legend{font-size:12px}",
            "</style>",
            f'<rect width="{width}" height="{height}" fill="#ffffff" />',
            f'<text x="20" y="36" class="title">{_esc(title)}</text>',
        ]
    )


def _svg_footer() -> str:
    return "</svg>\n"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a combined report and SVG figures from RAG evaluation outputs."
    )
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--records", type=Path, default=None)
    parser.add_argument("--key", type=Path, default=None)
    parser.add_argument("--answer-judgments", type=Path, default=None)
    parser.add_argument("--chunk-judgments", type=Path, default=None)
    parser.add_argument("--speed-summary", type=Path, default=None)
    parser.add_argument("--queries-json", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--metrics-json", type=Path, default=None)
    parser.add_argument("--metrics-csv", type=Path, default=None)
    parser.add_argument("--figures-dir", type=Path, default=None)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=123)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    (
        records_path,
        key_path,
        answer_judgments_path,
        chunk_judgments_path,
        speed_summary_path,
        output_path,
        metrics_json_path,
        metrics_csv_path,
        figures_dir,
    ) = resolve_paths(
        run_dir=args.run_dir,
        records=args.records,
        key=args.key,
        answer_judgments=args.answer_judgments,
        chunk_judgments=args.chunk_judgments,
        speed_summary=args.speed_summary,
        output=args.output,
        metrics_json=args.metrics_json,
        metrics_csv=args.metrics_csv,
        figures_dir=args.figures_dir,
    )
    generate_report(
        records_path=records_path,
        key_path=key_path,
        answer_judgments_path=answer_judgments_path,
        chunk_judgments_path=chunk_judgments_path,
        speed_summary_path=speed_summary_path,
        queries_json_path=args.queries_json,
        output_path=output_path,
        metrics_json_path=metrics_json_path,
        metrics_csv_path=metrics_csv_path,
        figures_dir=figures_dir,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
    )
    print(f"Wrote evaluation report to {output_path}")
    print(f"Wrote metrics JSON to {metrics_json_path}")
    print(f"Wrote metrics CSV to {metrics_csv_path}")
    print(f"Wrote figures to {figures_dir}")


if __name__ == "__main__":
    main()
