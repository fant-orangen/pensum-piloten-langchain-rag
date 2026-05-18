# Chunk Relevance Judgment Report

Judged chunks: 1500

Raw chunk judgments are blinded by method label. This report summarizes scores after joining with the review key.

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 1000 | 227 | 299 | 359 | 115 | 0 | 52.6% | 48.0% | 1.57 |
| reranked_rag | 250 | 86 | 80 | 66 | 18 | 0 | 66.4% | 61.2% | 1.84 |
| vector_rag | 250 | 93 | 76 | 67 | 14 | 0 | 67.6% | 64.0% | 1.92 |

Useful chunks are `direct_relevance` plus `support_relevance`.
Treat these labels as LLM-assisted proxy judgments unless manually validated.
