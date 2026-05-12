# Retrieval Evaluation Report

Queries: 50
Methods: `kg_rag`, `reranked_rag`, `vector_rag`
Review records: 150

This report joins anonymized records with `review_key.csv` for aggregate analysis. LLM-based judgments should be treated as proxy evidence unless manually validated.

## Figures

- [answer_overall_scores.svg](data/retrieval_review/run_20260510_170105/figures/answer_overall_scores.svg)
- [answer_rubric_scores.svg](data/retrieval_review/run_20260510_170105/figures/answer_rubric_scores.svg)
- [answer_winner_counts.svg](data/retrieval_review/run_20260510_170105/figures/answer_winner_counts.svg)
- [chunk_relevance_distribution.svg](data/retrieval_review/run_20260510_170105/figures/chunk_relevance_distribution.svg)
- [retrieval_latency_means.svg](data/retrieval_review/run_20260510_170105/figures/retrieval_latency_means.svg)
- [retrieval_chunk_overlap.svg](data/retrieval_review/run_20260510_170105/figures/retrieval_chunk_overlap.svg)

## Answer Judgment Summary

| Method | n | Correctness | Relevance | Clarity | Pedagogical | Faithfulness | Overall | 95% bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.22 | 4.90 | 4.80-4.98 |
| reranked_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.20 | 4.90 | 4.82-4.98 |
| vector_rag | 50 | 4.98 | 5.00 | 5.00 | 5.00 | 4.30 | 4.92 | 4.84-4.98 |

## Per-Question Winner Counts

| Winner | Count |
|---|---:|
| reranked_rag | 2 |
| tie | 47 |
| vector_rag | 1 |

## Chunk Relevance Summary

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 250 | 86 | 74 | 74 | 16 | 0 | 64.0% | 60.0% | 1.84 |
| reranked_rag | 250 | 86 | 79 | 69 | 16 | 0 | 66.0% | 61.2% | 1.86 |
| vector_rag | 250 | 89 | 79 | 68 | 14 | 0 | 67.2% | 63.6% | 1.90 |

## Retrieval Context Summary

| Method | n | Mean chunks | Mean unique sources | Mean answer characters |
|---|---:|---:|---:|---:|
| kg_rag | 50 | 5.00 | 1.30 | 1284 |
| reranked_rag | 50 | 5.00 | 1.44 | 1256 |
| vector_rag | 50 | 5.00 | 1.24 | 1269 |

## Retrieval Speed

| Method | n | Mean | Median | P95 | Max |
|---|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.869s | 0.822s | 1.176s | 1.728s |
| reranked_rag | 50 | 0.596s | 0.459s | 0.781s | 4.954s |
| vector_rag | 50 | 0.379s | 0.205s | 0.392s | 7.107s |

## Retrieved Chunk Overlap

Average per-query Jaccard similarity between final retrieved chunk sets.

| Method | kg_rag | reranked_rag | vector_rag |
|---|---:|---:|---:|
| kg_rag | 1.00 | 0.28 | 0.66 |
| reranked_rag | 0.28 | 1.00 | 0.36 |
| vector_rag | 0.66 | 0.36 | 1.00 |

## Interpretation Notes

- Normalized final context size helps prevent one method from winning by sending more chunks.
- Chunk judgments expose whether a method retrieves useful context before answer quality is considered.
- Overlap helps show whether methods are genuinely retrieving different evidence.
- Bootstrap intervals are descriptive and depend on the available judged examples.
