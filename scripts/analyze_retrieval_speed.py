"""Analyze retrieval latency by method from anonymized review outputs.

Usage:
    python -m scripts.analyze_retrieval_speed \
        --run-dir data/retrieval_review/run_20260510_120000
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class LatencyRecord:
    query_id: str
    method_label: str
    actual_method: str
    retrieval_latency_seconds: float


@dataclass(frozen=True, slots=True)
class LatencySummary:
    method: str
    count: int
    mean_seconds: float
    median_seconds: float
    min_seconds: float
    max_seconds: float
    stdev_seconds: float
    p25_seconds: float
    p75_seconds: float
    p95_seconds: float


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


def load_latency_records(records_path: Path, key_path: Path) -> list[LatencyRecord]:
    """Join anonymized review records with the de-anonymization key."""
    key = load_review_key(key_path)
    records: list[LatencyRecord] = []
    with records_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            query_id = _required_string(payload, "query_id", line_number)
            method_label = _required_string(payload, "method_label", line_number)
            actual_method = key.get((query_id, method_label))
            if actual_method is None:
                raise ValueError(
                    f"No review key entry for query_id={query_id!r}, "
                    f"method_label={method_label!r}."
                )
            records.append(
                LatencyRecord(
                    query_id=query_id,
                    method_label=method_label,
                    actual_method=actual_method,
                    retrieval_latency_seconds=_required_float(
                        payload,
                        "retrieval_latency_seconds",
                        line_number,
                    ),
                )
            )
    return records


def _required_string(payload: dict[str, Any], key: str, line_number: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Line {line_number} is missing non-empty string field {key!r}.")
    return value.strip()


def _required_float(payload: dict[str, Any], key: str, line_number: int) -> float:
    value = payload.get(key)
    if not isinstance(value, int | float):
        raise ValueError(f"Line {line_number} is missing numeric field {key!r}.")
    return float(value)


def summarize_latency(records: list[LatencyRecord]) -> list[LatencySummary]:
    """Compute latency summary statistics by actual method."""
    summaries: list[LatencySummary] = []
    for method in sorted({record.actual_method for record in records}):
        values = [
            record.retrieval_latency_seconds
            for record in records
            if record.actual_method == method
        ]
        summaries.append(
            LatencySummary(
                method=method,
                count=len(values),
                mean_seconds=statistics.fmean(values),
                median_seconds=statistics.median(values),
                min_seconds=min(values),
                max_seconds=max(values),
                stdev_seconds=statistics.stdev(values) if len(values) > 1 else 0.0,
                p25_seconds=_percentile(values, 0.25),
                p75_seconds=_percentile(values, 0.75),
                p95_seconds=_percentile(values, 0.95),
            )
        )
    return summaries


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        raise ValueError("Cannot compute percentile for an empty list.")
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = percentile * (len(sorted_values) - 1)
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    return sorted_values[lower_index] + (
        sorted_values[upper_index] - sorted_values[lower_index]
    ) * fraction


def write_markdown_report(
    summaries: list[LatencySummary],
    records: list[LatencyRecord],
    path: Path,
) -> None:
    """Write a thesis-friendly Markdown latency report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fastest = min(summaries, key=lambda summary: summary.mean_seconds, default=None)
    lines = [
        "# Retrieval Speed Analysis",
        "",
        f"Total retrieval records: {len(records)}",
        "",
    ]
    if fastest is not None:
        lines.extend(
            [
                f"Fastest method by mean latency: `{fastest.method}` "
                f"({_format_seconds(fastest.mean_seconds)}).",
                "",
            ]
        )

    lines.extend(
        [
            "## Summary By Method",
            "",
            "| Method | n | Mean | Median | Std. dev. | Min | P25 | P75 | P95 | Max |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for summary in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    summary.method,
                    str(summary.count),
                    _format_seconds(summary.mean_seconds),
                    _format_seconds(summary.median_seconds),
                    _format_seconds(summary.stdev_seconds),
                    _format_seconds(summary.min_seconds),
                    _format_seconds(summary.p25_seconds),
                    _format_seconds(summary.p75_seconds),
                    _format_seconds(summary.p95_seconds),
                    _format_seconds(summary.max_seconds),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Latency is measured by the review-generation script around retrieval only.",
            "- Answer generation latency is intentionally excluded from this report.",
            "- The join uses `query_id` plus anonymized `method_label`, because labels are shuffled per query.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json_summary(summaries: list[LatencySummary], path: Path) -> None:
    """Write machine-readable latency summary statistics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(summary) for summary in summaries], indent=2),
        encoding="utf-8",
    )


def _format_seconds(value: float) -> str:
    return f"{value:.3f}s"


def resolve_input_paths(
    *,
    run_dir: Path | None,
    records: Path | None,
    key: Path | None,
    output: Path | None,
    json_output: Path | None,
) -> tuple[Path, Path, Path, Path]:
    """Resolve input and output paths from a run directory or explicit files."""
    if run_dir is not None:
        return (
            records or run_dir / "review_records.jsonl",
            key or run_dir / "review_key.csv",
            output or run_dir / "retrieval_speed_report.md",
            json_output or run_dir / "retrieval_speed_summary.json",
        )
    return (
        records or Path("data/retrieval_review/review_records.jsonl"),
        key or Path("data/retrieval_review/review_key.csv"),
        output or Path("data/retrieval_review/retrieval_speed_report.md"),
        json_output or Path("data/retrieval_review/retrieval_speed_summary.json"),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze retrieval latency by method from anonymized review outputs."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Per-run output directory containing review_records.jsonl and review_key.csv.",
    )
    parser.add_argument(
        "--records",
        type=Path,
        default=None,
        help="Anonymized review_records.jsonl file.",
    )
    parser.add_argument(
        "--key",
        type=Path,
        default=None,
        help="De-anonymization review_key.csv file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Machine-readable JSON summary output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    records_path, key_path, output_path, json_output_path = resolve_input_paths(
        run_dir=args.run_dir,
        records=args.records,
        key=args.key,
        output=args.output,
        json_output=args.json_output,
    )
    records = load_latency_records(records_path, key_path)
    summaries = summarize_latency(records)
    write_markdown_report(summaries, records, output_path)
    write_json_summary(summaries, json_output_path)
    print(f"Wrote retrieval speed report to {output_path}")
    print(f"Wrote retrieval speed JSON summary to {json_output_path}")


if __name__ == "__main__":
    main()
