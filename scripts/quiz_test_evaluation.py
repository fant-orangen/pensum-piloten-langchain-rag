from pathlib import Path
import re
import pandas as pd

# Robust paths relative to this script file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "quiz"

FILES = {
    1: DATA_DIR / "memory_data.txt",
    2: DATA_DIR / "file_system_data.txt",
    3: DATA_DIR / "synchronisation_data.txt",
}

# Group-to-system order by topic position from the markdown
# Group 1: R-S-N
# Group 2: S-N-R
# Group 3: N-R-S
GROUP_PATTERNS = {
    1: ["R", "S", "N"],
    2: ["S", "N", "R"],
    3: ["N", "R", "S"],
}

# Username blocks mapped to topic sequences from the markdown
# u1-u4   => 1-2-3
# u5-u8   => 2-3-1
# u9-u12  => 3-1-2
def get_topic_sequence(user_number: int):
    if 1 <= user_number <= 4:
        return [1, 2, 3]
    elif 5 <= user_number <= 8:
        return [2, 3, 1]
    elif 9 <= user_number <= 12:
        return [3, 1, 2]
    else:
        raise ValueError(f"Unsupported user number: u{user_number}")

def parse_username(username: str):
    """
    Parse usernames like g1u1, g2u10, etc.
    Returns (group_number, user_number)
    """
    match = re.fullmatch(r"g(\d+)u(\d+)", str(username).strip())
    if not match:
        raise ValueError(f"Invalid username format: {username}")
    return int(match.group(1)), int(match.group(2))

def get_condition_for_subject(username: str, subject_topic: int) -> str:
    """
    Infer whether this student used R, S, or N for a given subject topic.
    """
    group_num, user_num = parse_username(username)
    if group_num not in GROUP_PATTERNS:
        raise ValueError(f"Unknown group: g{group_num}")

    topic_sequence = get_topic_sequence(user_num)
    pattern = GROUP_PATTERNS[group_num]

    # Find which position this subject occupies for the student
    # Example: topic_sequence [2,3,1], subject_topic=3 -> index 1 -> condition pattern[1]
    try:
        position = topic_sequence.index(subject_topic)
    except ValueError:
        raise ValueError(f"Subject topic {subject_topic} not found in topic sequence {topic_sequence}")

    return pattern[position]

def load_subject_file(file_path: Path, subject_topic: int) -> pd.DataFrame:
    """
    Expected format per row:
    respondent_id ; timestamp ; username ; q1 ; q2 ; ... ; duration_ms
    """
    df = pd.read_csv(file_path, sep=";", header=None, quotechar='"')

    if df.shape[1] < 5:
        raise ValueError(f"{file_path.name} has too few columns to be a valid quiz export.")

    num_cols = df.shape[1]
    num_question_cols = num_cols - 4  # respondent_id, timestamp, username, duration_ms

    columns = ["respondent_id", "timestamp", "username"]
    columns += [f"q{i}" for i in range(1, num_question_cols + 1)]
    columns += ["duration_ms"]

    df.columns = columns

    question_cols = [c for c in df.columns if c.startswith("q")]

    # Convert answers to numeric
    for col in question_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Score: 0 = correct, everything else = incorrect
    for col in question_cols:
        df[f"{col}_correct"] = (df[col] == 0).astype(int)

    correct_cols = [f"{col}_correct" for col in question_cols]
    df["num_correct"] = df[correct_cols].sum(axis=1)
    df["num_questions"] = len(question_cols)
    df["percent_correct"] = 100 * df["num_correct"] / df["num_questions"]

    # Determine which condition the student had for this subject
    df["subject_topic"] = subject_topic
    df["condition"] = df["username"].apply(lambda u: get_condition_for_subject(u, subject_topic))

    return df

def summarize_by_condition(all_data: pd.DataFrame) -> pd.DataFrame:
    summary = (
        all_data.groupby("condition")
        .agg(
            participants=("username", "count"),
            mean_correct=("num_correct", "mean"),
            mean_percent=("percent_correct", "mean"),
            std_percent=("percent_correct", "std"),
            total_correct=("num_correct", "sum"),
            total_questions=("num_questions", "sum"),
        )
        .reset_index()
    )

    summary["overall_percent"] = 100 * summary["total_correct"] / summary["total_questions"]

    condition_names = {
        "R": "RAG + system prompt",
        "S": "Improved system-prompt model",
        "N": "Basic chat system",
    }
    summary["condition_name"] = summary["condition"].map(condition_names)

    return summary[[
        "condition",
        "condition_name",
        "participants",
        "mean_correct",
        "mean_percent",
        "std_percent",
        "overall_percent",
    ]].sort_values("condition")

def summarize_by_subject_and_condition(all_data: pd.DataFrame) -> pd.DataFrame:
    summary = (
        all_data.groupby(["subject_topic", "condition"])
        .agg(
            participants=("username", "count"),
            mean_correct=("num_correct", "mean"),
            mean_percent=("percent_correct", "mean"),
        )
        .reset_index()
        .sort_values(["subject_topic", "condition"])
    )
    return summary

def print_interpretation(summary: pd.DataFrame):
    print("\n=== OVERALL INTERPRETATION ===")

    best_row = summary.sort_values("mean_percent", ascending=False).iloc[0]
    worst_row = summary.sort_values("mean_percent", ascending=True).iloc[0]

    print(
        f"Best average quiz performance: {best_row['condition']} "
        f"({best_row['condition_name']}) with mean score {best_row['mean_percent']:.2f}%."
    )
    print(
        f"Lowest average quiz performance: {worst_row['condition']} "
        f"({worst_row['condition_name']}) with mean score {worst_row['mean_percent']:.2f}%."
    )

    print("\nCondition ranking:")
    ranked = summary.sort_values("mean_percent", ascending=False)
    for i, (_, row) in enumerate(ranked.iterrows(), start=1):
        print(f"{i}. {row['condition']} - {row['condition_name']}: {row['mean_percent']:.2f}%")

def main():
    all_frames = []

    for topic, file_path in FILES.items():
        if not file_path.exists():
            print(f"Warning: Missing file for topic {topic}: {file_path}")
            continue

        df = load_subject_file(file_path, topic)
        all_frames.append(df)

    if not all_frames:
        raise FileNotFoundError("No input data files were found.")

    all_data = pd.concat(all_frames, ignore_index=True)

    overall_summary = summarize_by_condition(all_data)
    per_subject_summary = summarize_by_subject_and_condition(all_data)

    print("\n=== OVERALL SUMMARY BY CONDITION ===")
    print(overall_summary.to_string(index=False))

    print("\n=== SUMMARY BY SUBJECT AND CONDITION ===")
    print(per_subject_summary.to_string(index=False))

    print("\n=== PER-STUDENT RESULTS ===")
    print(
        all_data[
            ["username", "subject_topic", "condition", "num_correct", "num_questions", "percent_correct"]
        ].sort_values(["username", "subject_topic"]).to_string(index=False)
    )

    print_interpretation(overall_summary)

    # Save outputs
    output_dir = BASE_DIR / "data" / "quiz" / "analysis_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_data.to_csv(output_dir / "all_quiz_results.csv", index=False)
    overall_summary.to_csv(output_dir / "overall_summary_by_condition.csv", index=False)
    per_subject_summary.to_csv(output_dir / "summary_by_subject_and_condition.csv", index=False)

    print(f"\nSaved outputs to: {output_dir}")

if __name__ == "__main__":
    main()