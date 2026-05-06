import json

from scripts.analyze_model_preferences import (
    PreferenceRun,
    _format_p_value,
    analyze_consistency_by_evaluator,
    analyze_run,
    build_binomial_stats,
    exact_binomial_test_two_sided,
    load_preference_runs,
    summarize_by_evaluator,
    wilson_confidence_interval,
)


def test_load_preference_runs_from_json(tmp_path) -> None:
    path = tmp_path / "model_preferences.json"
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "evaluator": "Claude",
                        "run": 1,
                        "preferences": "A B,T",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert load_preference_runs(path) == [
        PreferenceRun(evaluator="Claude", run="1", preferences=["A", "B", "T"])
    ]


def test_analyze_run_counts_matches_against_true_labels() -> None:
    analysis = analyze_run(
        PreferenceRun(evaluator="ChatGPT", run="2", preferences=["A", "T", "B", "A"]),
        true_labels=["A", "B", "A", "A"],
    )

    assert analysis.compared == 4
    assert analysis.matches == 2
    assert analysis.mismatches == 1
    assert analysis.ties == 1
    assert analysis.decisive_accuracy == 2 / 3
    assert analysis.overall_accuracy == 0.5


def test_summarize_by_evaluator_aggregates_runs() -> None:
    analyses = [
        analyze_run(
            PreferenceRun(evaluator="Claude", run="1", preferences=["A", "B"]),
            true_labels=["A", "A"],
        ),
        analyze_run(
            PreferenceRun(evaluator="Claude", run="2", preferences=["T", "A"]),
            true_labels=["B", "A"],
        ),
    ]

    summaries = summarize_by_evaluator(analyses)

    assert len(summaries) == 1
    assert summaries[0].evaluator == "Claude"
    assert summaries[0].runs == 2
    assert summaries[0].matches == 2
    assert summaries[0].mismatches == 1
    assert summaries[0].ties == 1


def test_analyze_consistency_by_evaluator_counts_unanimous_answers() -> None:
    runs = [
        PreferenceRun(evaluator="Claude", run="1", preferences=["A", "B", "T", "A"]),
        PreferenceRun(evaluator="Claude", run="2", preferences=["A", "A", "T", "B"]),
        PreferenceRun(evaluator="Claude", run="3", preferences=["A", "B", "T"]),
        PreferenceRun(evaluator="Gemini", run="1", preferences=["A", "B", "T", "A"]),
    ]

    consistency = analyze_consistency_by_evaluator(runs, question_count=4)

    claude = next(row for row in consistency if row.evaluator == "Claude")
    assert claude.runs == 3
    assert claude.unanimous_answers == 2
    assert claude.differing_answers == 1
    assert claude.missing_positions == 1
    assert claude.unanimity_rate == 2 / 3

    gemini = next(row for row in consistency if row.evaluator == "Gemini")
    assert gemini.runs == 1
    assert gemini.unanimous_answers == 0
    assert gemini.differing_answers == 0
    assert gemini.missing_positions == 4


def test_wilson_confidence_interval_bounds_observed_rate() -> None:
    low, high = wilson_confidence_interval(successes=27, trials=39)

    assert round(low, 3) == 0.536
    assert round(high, 3) == 0.816


def test_exact_binomial_test_two_sided_against_even_coin() -> None:
    assert exact_binomial_test_two_sided(successes=5, trials=10) == 1.0
    assert round(exact_binomial_test_two_sided(successes=9, trials=10), 3) == 0.021


def test_build_binomial_stats_adds_pooled_row() -> None:
    analyses = [
        analyze_run(
            PreferenceRun(evaluator="Claude", run="1", preferences=["A", "B"]),
            true_labels=["A", "A"],
        ),
        analyze_run(
            PreferenceRun(evaluator="ChatGPT", run="1", preferences=["A", "A"]),
            true_labels=["A", "A"],
        ),
    ]
    summaries = summarize_by_evaluator(analyses)

    stats = build_binomial_stats(summaries)

    assert [row.label for row in stats] == ["ChatGPT", "Claude", "Pooled"]
    assert stats[-1].successes == 3
    assert stats[-1].trials == 4


def test_format_p_value_shows_exact_small_values() -> None:
    assert _format_p_value(0.000244140625) == "0.000244141"
    assert _format_p_value(0.03) == "0.03"
