# Chunk Relevance Judgment Report

Judged chunks: 750

Raw chunk judgments are blinded by method label. This report summarizes scores after joining with the review key.

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 250 | 86 | 74 | 74 | 16 | 0 | 64.0% | 60.0% | 1.84 |
| reranked_rag | 250 | 86 | 79 | 69 | 16 | 0 | 66.0% | 61.2% | 1.86 |
| vector_rag | 250 | 89 | 79 | 68 | 14 | 0 | 67.2% | 63.6% | 1.90 |

Useful chunks are `direct_relevance` plus `support_relevance`.
Treat these labels as LLM-assisted proxy judgments unless manually validated.
