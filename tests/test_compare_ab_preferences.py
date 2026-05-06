from scripts.compare_ab_preferences import (
    PreferenceComparison,
    compare_preferences,
    format_report,
)


def test_compare_preferences_counts_rag_matches_no_rag_matches_and_ties() -> None:
    result = compare_preferences(
        preferences=["A", "B", "T", "A", "B"],
        rag_labels=["A", "A", "B", "B", "B"],
    )

    assert result == PreferenceComparison(
        total_compared=5,
        rag_matches=2,
        no_rag_matches=2,
        ties=1,
        invalid_preferences=0,
        invalid_rag_labels=0,
        missing_preferences=0,
        missing_rag_labels=0,
    )
    assert result.rag_match_rate == 0.5
    assert result.overall_rag_match_rate == 0.4


def test_compare_preferences_tracks_mismatched_lengths_and_invalid_labels() -> None:
    result = compare_preferences(
        preferences=["A", "X", "B", "A"],
        rag_labels=["A", "B", "Z"],
    )

    assert result.rag_matches == 1
    assert result.invalid_preferences == 1
    assert result.invalid_rag_labels == 1
    assert result.missing_rag_labels == 1
    assert result.missing_preferences == 0


def test_format_report_includes_core_counts() -> None:
    report = format_report(
        PreferenceComparison(
            total_compared=4,
            rag_matches=2,
            no_rag_matches=1,
            ties=1,
            invalid_preferences=0,
            invalid_rag_labels=0,
            missing_preferences=0,
            missing_rag_labels=0,
        )
    )

    assert "Compared questions: 4" in report
    assert "RAG preferred: 2" in report
    assert "RAG preference rate, excluding ties: 66.7%" in report
