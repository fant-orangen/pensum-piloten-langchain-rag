# Answer Judgment Report

Judged answers: 15

Raw judgments are blinded by method label. This report summarizes scores after joining with the review key.

## Mean Scores By Method

| Method | n | Correctness | Relevance | Clarity | Pedagogical usefulness | Faithfulness | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 5 | 4.80 | 5.00 | 5.00 | 5.00 | 4.00 | 4.80 |
| reranked_rag | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 3.80 | 4.80 |
| vector_rag | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 4.20 | 5.00 |

## Rubric

- Scores range from 1 to 5.
- `faithfulness_to_chunks` measures support from the retrieved chunks, not external truth.
- Treat these scores as LLM-assisted proxy judgments, not human-grounded labels.
