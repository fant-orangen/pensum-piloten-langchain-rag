"""Analyze model preference runs against true/RAG A/B labels.

Usage:
    python -m scripts.analyze_model_preferences
    python -m scripts.analyze_model_preferences \
        --preferences data/ab_test/model_preferences.json \
        --true-labels data/ab_test/direct_labels.txt
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.compare_ab_preferences import compare_preferences, parse_label_file


@dataclass(frozen=True, slots=True)
class PreferenceRun:
    evaluator: str
    run: str
    preferences: list[str]


@dataclass(frozen=True, slots=True)
class RunAnalysis:
    evaluator: str
    run: str
    compared: int
    matches: int
    mismatches: int
    ties: int
    invalid_preferences: int
    missing_preferences: int
    extra_preferences: int

    @property
    def decisive_count(self) -> int:
        return self.matches + self.mismatches

    @property
    def decisive_accuracy(self) -> float:
        if self.decisive_count == 0:
            return 0.0
        return self.matches / self.decisive_count

    @property
    def overall_accuracy(self) -> float:
        if self.compared == 0:
            return 0.0
        return self.matches / self.compared


@dataclass(frozen=True, slots=True)
class EvaluatorSummary:
    evaluator: str
    runs: int
    compared: int
    matches: int
    mismatches: int
    ties: int
    invalid_preferences: int
    missing_preferences: int
    extra_preferences: int

    @property
    def decisive_count(self) -> int:
        return self.matches + self.mismatches

    @property
    def decisive_accuracy(self) -> float:
        if self.decisive_count == 0:
            return 0.0
        return self.matches / self.decisive_count

    @property
    def overall_accuracy(self) -> float:
        if self.compared == 0:
            return 0.0
        return self.matches / self.compared


@dataclass(frozen=True, slots=True)
class EvaluatorConsistency:
    evaluator: str
    runs: int
    questions_checked: int
    unanimous_answers: int
    differing_answers: int
    missing_positions: int

    @property
    def comparable_questions(self) -> int:
        return self.unanimous_answers + self.differing_answers

    @property
    def unanimity_rate(self) -> float:
        if self.comparable_questions == 0:
            return 0.0
        return self.unanimous_answers / self.comparable_questions


@dataclass(frozen=True, slots=True)
class BinomialStats:
    label: str
    successes: int
    trials: int
    wilson_low: float
    wilson_high: float
    exact_p_value: float

    @property
    def observed_rate(self) -> float:
        if self.trials == 0:
            return 0.0
        return self.successes / self.trials


def parse_preference_string(raw_preferences: str) -> list[str]:
    """Parse compact A/B/T preference strings, ignoring whitespace and commas."""
    labels: list[str] = []
    for char in raw_preferences.upper():
        if char.isspace() or char == ",":
            continue
        labels.append(char if char in {"A", "B", "T"} else f"INVALID:{char}")
    return labels


def load_preference_runs(path: Path) -> list[PreferenceRun]:
    """Load model preference runs from the JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Preference JSON must be an object.")

    raw_runs = payload.get("runs")
    if not isinstance(raw_runs, list):
        raise ValueError("Preference JSON must contain a 'runs' list.")

    runs: list[PreferenceRun] = []
    for index, raw_run in enumerate(raw_runs, start=1):
        if not isinstance(raw_run, dict):
            raise ValueError(f"Run {index} must be an object.")

        evaluator = _required_string(raw_run, "evaluator", index)
        run = str(raw_run.get("run", index))
        preferences = _required_string(raw_run, "preferences", index)
        runs.append(
            PreferenceRun(
                evaluator=evaluator,
                run=run,
                preferences=parse_preference_string(preferences),
            )
        )
    return runs


def _required_string(raw_run: dict[str, Any], key: str, index: int) -> str:
    value = raw_run.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Run {index} must contain a non-empty '{key}' string.")
    return value.strip()


def analyze_run(run: PreferenceRun, true_labels: list[str]) -> RunAnalysis:
    """Analyze one preference run against true labels."""
    comparison = compare_preferences(run.preferences, true_labels)
    return RunAnalysis(
        evaluator=run.evaluator,
        run=run.run,
        compared=comparison.total_compared,
        matches=comparison.rag_matches,
        mismatches=comparison.no_rag_matches,
        ties=comparison.ties,
        invalid_preferences=comparison.invalid_preferences,
        missing_preferences=comparison.missing_preferences,
        extra_preferences=comparison.missing_rag_labels,
    )


def summarize_by_evaluator(analyses: list[RunAnalysis]) -> list[EvaluatorSummary]:
    """Aggregate run analyses by evaluator."""
    evaluators = sorted({analysis.evaluator for analysis in analyses})
    summaries: list[EvaluatorSummary] = []
    for evaluator in evaluators:
        rows = [analysis for analysis in analyses if analysis.evaluator == evaluator]
        summaries.append(
            EvaluatorSummary(
                evaluator=evaluator,
                runs=len(rows),
                compared=sum(row.compared for row in rows),
                matches=sum(row.matches for row in rows),
                mismatches=sum(row.mismatches for row in rows),
                ties=sum(row.ties for row in rows),
                invalid_preferences=sum(row.invalid_preferences for row in rows),
                missing_preferences=sum(row.missing_preferences for row in rows),
                extra_preferences=sum(row.extra_preferences for row in rows),
            )
        )
    return summaries


def analyze_consistency_by_evaluator(
    runs: list[PreferenceRun],
    *,
    question_count: int,
) -> list[EvaluatorConsistency]:
    """Count how often each evaluator gives the same answer across its runs."""
    evaluators = sorted({run.evaluator for run in runs})
    consistency: list[EvaluatorConsistency] = []

    for evaluator in evaluators:
        evaluator_runs = [run for run in runs if run.evaluator == evaluator]
        if len(evaluator_runs) < 2:
            consistency.append(
                EvaluatorConsistency(
                    evaluator=evaluator,
                    runs=len(evaluator_runs),
                    questions_checked=question_count,
                    unanimous_answers=0,
                    differing_answers=0,
                    missing_positions=question_count,
                )
            )
            continue

        unanimous_answers = 0
        differing_answers = 0
        missing_positions = 0

        for index in range(question_count):
            labels = [
                run.preferences[index]
                for run in evaluator_runs
                if index < len(run.preferences)
            ]
            if len(labels) != len(evaluator_runs):
                missing_positions += 1
                continue
            if len(set(labels)) == 1:
                unanimous_answers += 1
            else:
                differing_answers += 1

        consistency.append(
            EvaluatorConsistency(
                evaluator=evaluator,
                runs=len(evaluator_runs),
                questions_checked=question_count,
                unanimous_answers=unanimous_answers,
                differing_answers=differing_answers,
                missing_positions=missing_positions,
            )
        )

    return consistency


def wilson_confidence_interval(
    successes: int,
    trials: int,
    *,
    z: float = 1.959963984540054,
) -> tuple[float, float]:
    """Return the Wilson score confidence interval for a binomial proportion."""
    if trials == 0:
        return 0.0, 0.0

    proportion = successes / trials
    z_squared = z * z
    denominator = 1 + z_squared / trials
    centre = proportion + z_squared / (2 * trials)
    margin = z * math.sqrt(
        (proportion * (1 - proportion) + z_squared / (4 * trials)) / trials
    )
    return (centre - margin) / denominator, (centre + margin) / denominator


def exact_binomial_test_two_sided(successes: int, trials: int, *, p: float = 0.5) -> float:
    """Return the exact two-sided binomial-test p-value for H0: probability == p."""
    if trials == 0:
        return 1.0

    observed_probability = _binomial_probability(successes, trials, p)
    p_value = 0.0
    tolerance = 1e-15
    for candidate_successes in range(trials + 1):
        probability = _binomial_probability(candidate_successes, trials, p)
        if probability <= observed_probability + tolerance:
            p_value += probability
    return min(1.0, p_value)


def _binomial_probability(successes: int, trials: int, p: float) -> float:
    return math.comb(trials, successes) * (p**successes) * ((1 - p) ** (trials - successes))


def build_binomial_stats(summaries: list[EvaluatorSummary]) -> list[BinomialStats]:
    """Build per-evaluator and pooled Wilson/binomial statistics."""
    rows: list[BinomialStats] = []
    for summary in summaries:
        rows.append(_make_binomial_stats(summary.evaluator, summary.matches, summary.decisive_count))

    pooled_successes = sum(summary.matches for summary in summaries)
    pooled_trials = sum(summary.decisive_count for summary in summaries)
    rows.append(_make_binomial_stats("Pooled", pooled_successes, pooled_trials))
    return rows


def _make_binomial_stats(label: str, successes: int, trials: int) -> BinomialStats:
    wilson_low, wilson_high = wilson_confidence_interval(successes, trials)
    return BinomialStats(
        label=label,
        successes=successes,
        trials=trials,
        wilson_low=wilson_low,
        wilson_high=wilson_high,
        exact_p_value=exact_binomial_test_two_sided(successes, trials),
    )


def format_report(
    analyses: list[RunAnalysis],
    summaries: list[EvaluatorSummary],
    consistency: list[EvaluatorConsistency],
    binomial_stats: list[BinomialStats],
) -> str:
    """Format a readable report."""
    lines = ["Per-run analysis:"]
    lines.extend(
        _format_table(
            headers=[
                "Evaluator",
                "Run",
                "Compared",
                "Matches",
                "Mismatches",
                "Ties",
                "Accuracy excl. ties",
                "Accuracy incl. ties",
            ],
            rows=[
                [
                    row.evaluator,
                    row.run,
                    str(row.compared),
                    str(row.matches),
                    str(row.mismatches),
                    str(row.ties),
                    _format_percent(row.decisive_accuracy),
                    _format_percent(row.overall_accuracy),
                ]
                for row in analyses
            ],
        )
    )
    lines.append("")
    lines.append("By evaluator:")
    lines.extend(
        _format_table(
            headers=[
                "Evaluator",
                "Runs",
                "Compared",
                "Matches",
                "Mismatches",
                "Ties",
                "Accuracy excl. ties",
                "Accuracy incl. ties",
            ],
            rows=[
                [
                    row.evaluator,
                    str(row.runs),
                    str(row.compared),
                    str(row.matches),
                    str(row.mismatches),
                    str(row.ties),
                    _format_percent(row.decisive_accuracy),
                    _format_percent(row.overall_accuracy),
                ]
                for row in summaries
            ],
        )
    )
    lines.append("")
    lines.append("Wilson CI and exact binomial test vs 50% (ties excluded):")
    lines.extend(
        _format_table(
            headers=[
                "Evaluator",
                "Matches",
                "Decisive n",
                "Observed",
                "95% Wilson CI",
                "Exact p",
            ],
            rows=[
                [
                    row.label,
                    str(row.successes),
                    str(row.trials),
                    _format_percent(row.observed_rate),
                    f"{_format_percent(row.wilson_low)} - {_format_percent(row.wilson_high)}",
                    _format_p_value(row.exact_p_value),
                ]
                for row in binomial_stats
            ],
        )
    )
    lines.append("")
    lines.append("Within-evaluator consistency:")
    lines.extend(
        _format_table(
            headers=[
                "Evaluator",
                "Runs",
                "Questions",
                "Same across runs",
                "Different across runs",
                "Missing positions",
                "Same-rate excl. missing",
            ],
            rows=[
                [
                    row.evaluator,
                    str(row.runs),
                    str(row.questions_checked),
                    str(row.unanimous_answers),
                    str(row.differing_answers),
                    str(row.missing_positions),
                    _format_percent(row.unanimity_rate),
                ]
                for row in consistency
            ],
        )
    )

    invalid_total = sum(row.invalid_preferences for row in analyses)
    missing_total = sum(row.missing_preferences for row in analyses)
    extra_total = sum(row.extra_preferences for row in analyses)
    if invalid_total or missing_total or extra_total:
        lines.append("")
        lines.append("Data quality:")
        lines.append(f"Invalid preference labels: {invalid_total}")
        lines.append(f"Missing preferences: {missing_total}")
        lines.append(f"Extra preferences beyond true labels: {extra_total}")

    return "\n".join(lines)


def _format_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [
        max(len(headers[column]), *(len(row[column]) for row in rows))
        if rows
        else len(headers[column])
        for column in range(len(headers))
    ]
    formatted = ["  " + "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))]
    formatted.append("  " + "  ".join("-" * width for width in widths))
    formatted.extend(
        "  " + "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return formatted


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _format_p_value(value: float) -> str:
    return f"{value:.6g}"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze JSON model preference runs against true/RAG A/B labels."
    )
    parser.add_argument(
        "--preferences",
        type=Path,
        default=Path("data/ab_test/model_preferences.json"),
        help="JSON file containing evaluator preference runs.",
    )
    parser.add_argument(
        "--true-labels",
        type=Path,
        default=Path("data/ab_test/direct_labels.txt"),
        help="Compact true/RAG labels in question order. Supports A and B.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    true_labels = parse_label_file(args.true_labels, valid_labels={"A", "B"})
    runs = load_preference_runs(args.preferences)
    analyses = [analyze_run(run, true_labels) for run in runs]
    summaries = summarize_by_evaluator(analyses)
    consistency = analyze_consistency_by_evaluator(runs, question_count=len(true_labels))
    binomial_stats = build_binomial_stats(summaries)
    print(format_report(analyses, summaries, consistency, binomial_stats))


if __name__ == "__main__":
    main()
