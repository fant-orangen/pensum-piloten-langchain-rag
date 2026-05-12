# Answer Judgment Report

Judged answers: 150

Raw judgments are blinded by method label. This report summarizes scores after joining with the review key.

## Mean Scores By Method

| Method | n | Correctness | Relevance | Clarity | Pedagogical usefulness | Faithfulness | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.22 | 4.90 |
| reranked_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.20 | 4.90 |
| vector_rag | 50 | 4.98 | 5.00 | 5.00 | 5.00 | 4.30 | 4.92 |

## Rubric

- Scores range from 1 to 5.
- `faithfulness_to_chunks` measures support from the retrieved chunks, not external truth.
- Treat these scores as LLM-assisted proxy judgments, not human-grounded labels.
