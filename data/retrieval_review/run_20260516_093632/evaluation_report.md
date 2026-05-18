# Retrieval Evaluation Report

Queries: 50
Methods: `kg_rag`, `reranked_rag`, `vector_rag`
Review records: 150

This report joins anonymized records with `review_key.csv` for aggregate analysis. LLM-based judgments should be treated as proxy evidence unless manually validated.

## Figures

- [answer_overall_scores.svg](data/retrieval_review/run_20260516_093632/figures/answer_overall_scores.svg)
- [answer_rubric_scores.svg](data/retrieval_review/run_20260516_093632/figures/answer_rubric_scores.svg)
- [answer_winner_counts.svg](data/retrieval_review/run_20260516_093632/figures/answer_winner_counts.svg)
- [chunk_relevance_distribution.svg](data/retrieval_review/run_20260516_093632/figures/chunk_relevance_distribution.svg)
- [retrieval_latency_means.svg](data/retrieval_review/run_20260516_093632/figures/retrieval_latency_means.svg)
- [retrieval_chunk_overlap.svg](data/retrieval_review/run_20260516_093632/figures/retrieval_chunk_overlap.svg)

## Answer Judgment Summary

| Method | n | Correctness | Relevance | Clarity | Pedagogical | Faithfulness | Overall | 95% bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.64 | 4.98 | 4.94-5.00 |
| reranked_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.68 | 4.98 | 4.94-5.00 |
| vector_rag | 50 | 4.98 | 5.00 | 5.00 | 5.00 | 4.66 | 4.98 | 4.94-5.00 |

## Per-Question Winner Counts

| Winner | Count |
|---|---:|
| tie | 50 |

## Chunk Relevance Summary

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 1000 | 232 | 291 | 359 | 118 | 0 | 52.3% | 46.1% | 1.57 |
| reranked_rag | 1000 | 233 | 289 | 359 | 119 | 0 | 52.2% | 47.5% | 1.57 |
| vector_rag | 1000 | 236 | 290 | 361 | 113 | 0 | 52.6% | 46.1% | 1.57 |

## Retrieval Context Summary

| Method | n | Mean chunks | Mean unique sources | Mean answer characters |
|---|---:|---:|---:|---:|
| kg_rag | 50 | 20.00 | 2.04 | 1358 |
| reranked_rag | 50 | 20.00 | 2.36 | 1359 |
| vector_rag | 50 | 20.00 | 2.18 | 1315 |

## Retrieval Speed

| Method | n | Mean | Median | P95 | Max |
|---|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.834s | 0.798s | 0.994s | 2.063s |
| reranked_rag | 50 | 0.587s | 0.440s | 0.856s | 5.181s |
| vector_rag | 50 | 0.385s | 0.208s | 0.452s | 7.455s |

## Retrieved Chunk Overlap

Average per-query Jaccard similarity between final retrieved chunk sets.

| Method | kg_rag | reranked_rag | vector_rag |
|---|---:|---:|---:|
| kg_rag | 1.00 | 0.57 | 0.73 |
| reranked_rag | 0.57 | 1.00 | 0.61 |
| vector_rag | 0.73 | 0.61 | 1.00 |

## Interpretation Notes

- Normalized final context size helps prevent one method from winning by sending more chunks.
- Chunk judgments expose whether a method retrieves useful context before answer quality is considered.
- Overlap helps show whether methods are genuinely retrieving different evidence.
- Bootstrap intervals are descriptive and depend on the available judged examples.
