import pandas as pd
from pathlib import Path

# Path to your survey export
FILE_PATH = "../data/ab_test/ab_data.txt"

# Question order:
# True  = RAG shown first, non-RAG shown second
# False = non-RAG shown first, RAG shown second
RAG_FIRST = [True, True, False, True, False, True]

def analyze_survey(file_path: str) -> None:
    # File format inferred from your export:
    # respondent_id ; timestamp ; name ; q1 ; q2 ; q3 ; q4 ; q5 ; q6 ; duration_ms
    df = pd.read_csv(file_path, sep=";", header=None, quotechar='"')

    df.columns = [
        "respondent_id",
        "timestamp",
        "name",
        "q1", "q2", "q3", "q4", "q5", "q6",
        "duration_ms",
    ]

    question_cols = [f"q{i}" for i in range(1, 7)]

    # Convert raw slider values to integers
    for col in question_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize every answer so that:
    #   positive  => preference for RAG
    #   negative  => preference for non-RAG
    #   zero      => tie / no preference
    normalized_cols = []

    for i, col in enumerate(question_cols):
        norm_col = f"{col}_rag_preference"
        if RAG_FIRST[i]:
            # If RAG is first, invert sign so positive always means RAG
            df[norm_col] = -df[col]
        else:
            # If RAG is second, keep sign as-is
            df[norm_col] = df[col]
        normalized_cols.append(norm_col)

    # Per-respondent overall score
    df["overall_rag_score"] = df[normalized_cols].mean(axis=1)

    # Summary statistics
    overall_mean = df["overall_rag_score"].mean()
    overall_sum = df[normalized_cols].to_numpy().mean()

    total_comparisons = df[normalized_cols].count().sum()
    rag_wins = (df[normalized_cols] > 0).sum().sum()
    nonrag_wins = (df[normalized_cols] < 0).sum().sum()
    ties = (df[normalized_cols] == 0).sum().sum()

    print("\n=== OVERALL EVALUATION ===")
    print(f"Number of respondents: {len(df)}")
    print(f"Number of answered comparisons: {total_comparisons}")
    print(f"Mean normalized score (positive = RAG better): {overall_sum:.3f}")

    if overall_sum > 0:
        print("Interpretation: Students preferred the RAG solution overall.")
    elif overall_sum < 0:
        print("Interpretation: Students preferred the non-RAG solution overall.")
    else:
        print("Interpretation: No overall preference between RAG and non-RAG.")

    print("\n=== COMPARISON COUNTS ===")
    print(f"RAG preferred:     {rag_wins}")
    print(f"non-RAG preferred: {nonrag_wins}")
    print(f"Ties:              {ties}")

    print("\n=== PER-QUESTION MEAN (positive = RAG better) ===")
    for i, col in enumerate(normalized_cols, start=1):
        print(f"Question {i}: {df[col].mean():.3f}")

    print("\n=== PER-RESPONDENT OVERALL SCORE ===")
    print(df[["respondent_id", "name", "overall_rag_score"]].to_string(index=False))

    # Optional: save normalized data
    output_path = Path(file_path).with_name("survey_analysis_output.csv")
    df.to_csv(output_path, index=False)
    print(f"\nSaved detailed output to: {output_path}")

if __name__ == "__main__":
    analyze_survey(FILE_PATH)