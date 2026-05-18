# Chunk Relevance Judgment Report

Judged chunks: 3000

Raw chunk judgments are blinded by method label. This report summarizes scores after joining with the review key.

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 1000 | 232 | 291 | 359 | 118 | 0 | 52.3% | 46.1% | 1.57 |
| reranked_rag | 1000 | 233 | 289 | 359 | 119 | 0 | 52.2% | 47.5% | 1.57 |
| vector_rag | 1000 | 236 | 290 | 361 | 113 | 0 | 52.6% | 46.1% | 1.57 |

Useful chunks are `direct_relevance` plus `support_relevance`.
Treat these labels as LLM-assisted proxy judgments unless manually validated.
