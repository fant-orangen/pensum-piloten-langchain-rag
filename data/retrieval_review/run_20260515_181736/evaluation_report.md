# Retrieval Evaluation Report

Queries: 50
Methods: `kg_rag`, `reranked_rag`, `vector_rag`
Review records: 150

This report joins anonymized records with `review_key.csv` for aggregate analysis. LLM-based judgments should be treated as proxy evidence unless manually validated.

## Figures

- [answer_overall_scores.svg](data/retrieval_review/run_20260515_181736/figures/answer_overall_scores.svg)
- [answer_rubric_scores.svg](data/retrieval_review/run_20260515_181736/figures/answer_rubric_scores.svg)
- [answer_winner_counts.svg](data/retrieval_review/run_20260515_181736/figures/answer_winner_counts.svg)
- [chunk_relevance_distribution.svg](data/retrieval_review/run_20260515_181736/figures/chunk_relevance_distribution.svg)
- [retrieval_latency_means.svg](data/retrieval_review/run_20260515_181736/figures/retrieval_latency_means.svg)
- [retrieval_chunk_overlap.svg](data/retrieval_review/run_20260515_181736/figures/retrieval_chunk_overlap.svg)

## Answer Judgment Summary

| Method | n | Correctness | Relevance | Clarity | Pedagogical | Faithfulness | Overall | 95% bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 5.00 | 5.00 | 4.98 | 5.00 | 4.66 | 4.98 | 4.94-5.00 |
| reranked_rag | 50 | 5.00 | 5.00 | 5.00 | 5.00 | 4.20 | 4.90 | 4.82-4.98 |
| vector_rag | 50 | 4.98 | 5.00 | 5.00 | 5.00 | 4.30 | 4.90 | 4.82-4.98 |

## Per-Question Winner Counts

| Winner | Count |
|---|---:|
| kg_rag | 1 |
| tie | 49 |

## Chunk Relevance Summary

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 1000 | 227 | 299 | 359 | 115 | 0 | 52.6% | 48.0% | 1.57 |
| reranked_rag | 250 | 86 | 80 | 66 | 18 | 0 | 66.4% | 61.2% | 1.84 |
| vector_rag | 250 | 93 | 76 | 67 | 14 | 0 | 67.6% | 64.0% | 1.92 |

## Retrieval Context Summary

| Method | n | Mean chunks | Mean unique sources | Mean answer characters |
|---|---:|---:|---:|---:|
| kg_rag | 50 | 20.00 | 2.04 | 1294 |
| reranked_rag | 50 | 5.00 | 1.44 | 1265 |
| vector_rag | 50 | 5.00 | 1.24 | 1228 |

## Retrieval Speed

| Method | n | Mean | Median | P95 | Max |
|---|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.752s | 0.752s | 1.030s | 1.219s |
| reranked_rag | 50 | 0.504s | 0.368s | 0.678s | 5.690s |
| vector_rag | 50 | 0.390s | 0.208s | 0.395s | 8.526s |

## Retrieved Chunk Overlap

Average per-query Jaccard similarity between final retrieved chunk sets.

| Method | kg_rag | reranked_rag | vector_rag |
|---|---:|---:|---:|
| kg_rag | 1.00 | 0.21 | 0.24 |
| reranked_rag | 0.21 | 1.00 | 0.36 |
| vector_rag | 0.24 | 0.36 | 1.00 |

## Interpretation Notes

- Normalized final context size helps prevent one method from winning by sending more chunks.
- Chunk judgments expose whether a method retrieves useful context before answer quality is considered.
- Overlap helps show whether methods are genuinely retrieving different evidence.
- Bootstrap intervals are descriptive and depend on the available judged examples.
