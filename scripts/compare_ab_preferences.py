"""Compare blinded model preferences against RAG answer labels.

Usage:
    python -m scripts.compare_ab_preferences
    python -m scripts.compare_ab_preferences \
        --preferences data/ab_test/chatbot_preference.txt \
        --rag-labels data/ab_test/direct_labels.txt
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

PreferenceLabel = str
AnswerLabel = str


@dataclass(frozen=True, slots=True)
class PreferenceComparison:
    total_compared: int
    rag_matches: int
    no_rag_matches: int
    ties: int
    invalid_preferences: int
    invalid_rag_labels: int
    missing_preferences: int
    missing_rag_labels: int

    @property
    def decisive_preferences(self) -> int:
        return self.rag_matches + self.no_rag_matches

    @property
    def rag_match_rate(self) -> float:
        if self.decisive_preferences == 0:
            return 0.0
        return self.rag_matches / self.decisive_preferences

    @property
    def overall_rag_match_rate(self) -> float:
        if self.total_compared == 0:
            return 0.0
        return self.rag_matches / self.total_compared


def parse_label_file(path: Path, *, valid_labels: set[str]) -> list[str]:
    """Read compact A/B/T label files, ignoring whitespace and commas."""
    raw_text = path.read_text(encoding="utf-8")
    labels: list[str] = []
    for char in raw_text.upper():
        if char.isspace() or char == ",":
            continue
        labels.append(char if char in valid_labels else f"INVALID:{char}")
    return labels


def compare_preferences(
    preferences: list[PreferenceLabel],
    rag_labels: list[AnswerLabel],
) -> PreferenceComparison:
    """Compare preference labels with RAG labels in question order."""
    total_compared = min(len(preferences), len(rag_labels))
    rag_matches = 0
    no_rag_matches = 0
    ties = 0
    invalid_preferences = 0
    invalid_rag_labels = 0

    for preference, rag_label in zip(preferences[:total_compared], rag_labels[:total_compared]):
        if preference not in {"A", "B", "T"}:
            invalid_preferences += 1
            continue
        if rag_label not in {"A", "B"}:
            invalid_rag_labels += 1
            continue
        if preference == "T":
            ties += 1
        elif preference == rag_label:
            rag_matches += 1
        else:
            no_rag_matches += 1

    return PreferenceComparison(
        total_compared=total_compared,
        rag_matches=rag_matches,
        no_rag_matches=no_rag_matches,
        ties=ties,
        invalid_preferences=invalid_preferences,
        invalid_rag_labels=invalid_rag_labels,
        missing_preferences=max(0, len(rag_labels) - len(preferences)),
        missing_rag_labels=max(0, len(preferences) - len(rag_labels)),
    )


def format_report(result: PreferenceComparison) -> str:
    """Format a human-readable comparison report."""
    return "\n".join(
        [
            f"Compared questions: {result.total_compared}",
            f"RAG preferred: {result.rag_matches}",
            f"No-RAG preferred: {result.no_rag_matches}",
            f"Ties: {result.ties}",
            f"RAG preference rate, excluding ties: {result.rag_match_rate:.1%}",
            f"RAG preference rate, including ties in denominator: {result.overall_rag_match_rate:.1%}",
            f"Invalid preference labels: {result.invalid_preferences}",
            f"Invalid RAG labels: {result.invalid_rag_labels}",
            f"Missing preferences: {result.missing_preferences}",
            f"Missing RAG labels: {result.missing_rag_labels}",
        ]
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare chatbot preference labels with RAG A/B labels."
    )
    parser.add_argument(
        "--preferences",
        type=Path,
        default=Path("data/ab_test/chatbot_preference.txt"),
        help="Compact model preference labels in question order. Supports A, B, and T.",
    )
    parser.add_argument(
        "--rag-labels",
        type=Path,
        default=Path("data/ab_test/direct_labels.txt"),
        help="Compact RAG answer labels in question order. Supports A and B.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    preferences = parse_label_file(args.preferences, valid_labels={"A", "B", "T"})
    rag_labels = parse_label_file(args.rag_labels, valid_labels={"A", "B"})
    result = compare_preferences(preferences, rag_labels)
    print(format_report(result))


if __name__ == "__main__":
    main()
