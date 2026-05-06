import csv

from scripts.generate_blinded_direct_ab_answers import (
    GeneratedAnswerPair,
    Question,
    build_direct_label_plan,
    build_primary_label_plan,
    format_blinded_answers,
    parse_questions,
    write_answer_key,
    write_direct_label_list,
)


def test_parse_questions_accepts_dot_and_parenthesis_numbering() -> None:
    raw_text = """
    1. What is a process?
       Include the relationship to memory.

    2) What is a thread?
    """

    assert parse_questions(raw_text) == [
        Question(number=1, text="What is a process? Include the relationship to memory."),
        Question(number=2, text="What is a thread?"),
    ]


def test_build_direct_label_plan_is_balanced() -> None:
    labels = build_direct_label_plan(5, seed=7)

    assert sorted(labels) == ["A", "A", "B", "B", "B"]
    assert labels == build_primary_label_plan(5, seed=7)


def test_format_blinded_answers_and_key_outputs(tmp_path) -> None:
    records = [
        GeneratedAnswerPair(
            question=Question(number=1, text="What is virtual memory?"),
            answer_a="Direct answer",
            answer_b="Control answer",
            source_a="direct_system_prompt",
            source_b="no_rag_control",
            primary_latency_seconds=1.23456,
            baseline_latency_seconds=2.34567,
            primary_source="direct_system_prompt",
            baseline_source="no_rag_control",
            primary_prompt_variant="default",
            baseline_prompt_variant="control",
            comparison="direct-vs-control",
        ),
        GeneratedAnswerPair(
            question=Question(number=2, text="What is a syscall?"),
            answer_a="Control answer 2",
            answer_b="Direct answer 2",
            source_a="no_rag_control",
            source_b="direct_system_prompt",
            primary_latency_seconds=3.0,
            baseline_latency_seconds=4.0,
            primary_source="direct_system_prompt",
            baseline_source="no_rag_control",
            primary_prompt_variant="default",
            baseline_prompt_variant="control",
            comparison="direct-vs-control",
        ),
    ]

    assert format_blinded_answers(records) == (
        "1. What is virtual memory?\n"
        "A)\n"
        "Direct answer\n"
        "B)\n"
        "Control answer\n"
        "\n"
        "2. What is a syscall?\n"
        "A)\n"
        "Control answer 2\n"
        "B)\n"
        "Direct answer 2\n"
    )

    key_path = tmp_path / "keys" / "answer_key.csv"
    labels_path = tmp_path / "keys" / "direct_labels.txt"
    write_answer_key(records, key_path)
    write_direct_label_list(records, labels_path)

    with key_path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["direct_label"] == "A"
    assert rows[0]["control_label"] == "B"
    assert rows[0]["primary_label"] == "A"
    assert rows[0]["baseline_label"] == "B"
    assert rows[0]["no_rag_label"] == ""
    assert rows[0]["primary_latency_seconds"] == "1.235"
    assert rows[1]["direct_label"] == "B"
    assert rows[1]["control_label"] == "A"
    assert rows[1]["no_rag_label"] == ""
    assert labels_path.read_text(encoding="utf-8") == "AB\n"


def test_answer_key_outputs_rag_labels_when_comparing_rag_to_no_rag(tmp_path) -> None:
    records = [
        GeneratedAnswerPair(
            question=Question(number=1, text="What is paging?"),
            answer_a="No-RAG answer",
            answer_b="RAG answer",
            source_a="no_rag",
            source_b="rag",
            primary_latency_seconds=5.0,
            baseline_latency_seconds=2.0,
            primary_source="rag",
            baseline_source="no_rag",
            primary_prompt_variant="default",
            baseline_prompt_variant="default",
            comparison="rag-vs-no-rag",
            chroma_collection="os_g1",
            graph_scope="os_g1",
        )
    ]

    key_path = tmp_path / "answer_key.csv"
    labels_path = tmp_path / "rag_labels.txt"
    write_answer_key(records, key_path)
    write_direct_label_list(records, labels_path)

    with key_path.open(encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))

    assert row["comparison"] == "rag-vs-no-rag"
    assert row["rag_label"] == "B"
    assert row["no_rag_label"] == "A"
    assert row["primary_label"] == "B"
    assert row["baseline_label"] == "A"
    assert row["chroma_collection"] == "os_g1"
    assert labels_path.read_text(encoding="utf-8") == "B\n"
