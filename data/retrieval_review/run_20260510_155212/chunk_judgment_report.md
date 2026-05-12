# Chunk Relevance Judgment Report

Judged chunks: 75

Raw chunk judgments are blinded by method label. This report summarizes scores after joining with the review key.

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 25 | 6 | 8 | 9 | 2 | 0 | 56.0% | 52.0% | 1.60 |
| reranked_rag | 25 | 3 | 14 | 7 | 1 | 0 | 68.0% | 60.0% | 1.64 |
| vector_rag | 25 | 4 | 10 | 10 | 1 | 0 | 56.0% | 44.0% | 1.48 |

Useful chunks are `direct_relevance` plus `support_relevance`.
Treat these labels as LLM-assisted proxy judgments unless manually validated.
