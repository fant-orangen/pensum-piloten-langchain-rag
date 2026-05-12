# Retrieval Evaluation Report

Queries: 5
Methods: `kg_rag`, `reranked_rag`, `vector_rag`
Review records: 15

This report joins anonymized records with `review_key.csv` for aggregate analysis. LLM-based judgments should be treated as proxy evidence unless manually validated.

## Figures

- [answer_overall_scores.svg](data/retrieval_review/run_20260510_155212/figures/answer_overall_scores.svg)
- [answer_rubric_scores.svg](data/retrieval_review/run_20260510_155212/figures/answer_rubric_scores.svg)
- [answer_winner_counts.svg](data/retrieval_review/run_20260510_155212/figures/answer_winner_counts.svg)
- [chunk_relevance_distribution.svg](data/retrieval_review/run_20260510_155212/figures/chunk_relevance_distribution.svg)
- [retrieval_latency_means.svg](data/retrieval_review/run_20260510_155212/figures/retrieval_latency_means.svg)
- [retrieval_chunk_overlap.svg](data/retrieval_review/run_20260510_155212/figures/retrieval_chunk_overlap.svg)

## Answer Judgment Summary

| Method | n | Correctness | Relevance | Clarity | Pedagogical | Faithfulness | Overall | 95% bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 5 | 4.80 | 5.00 | 5.00 | 5.00 | 4.00 | 4.80 | 4.40-5.00 |
| reranked_rag | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 3.80 | 4.80 | 4.40-5.00 |
| vector_rag | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 4.20 | 5.00 | 5.00-5.00 |

## Per-Question Winner Counts

| Winner | Count |
|---|---:|
| tie | 5 |

## Chunk Relevance Summary

| Method | n | Direct | Support | Marginal | Irrelevant | Redundant | Useful rate | Include rate | Mean usefulness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 25 | 6 | 6 | 11 | 2 | 0 | 48.0% | 48.0% | 1.56 |
| reranked_rag | 25 | 2 | 12 | 9 | 2 | 0 | 56.0% | 52.0% | 1.52 |
| vector_rag | 25 | 3 | 11 | 10 | 1 | 0 | 56.0% | 52.0% | 1.56 |

## Retrieval Context Summary

| Method | n | Mean chunks | Mean unique sources | Mean answer characters |
|---|---:|---:|---:|---:|
| kg_rag | 5 | 5.00 | 1.20 | 1524 |
| reranked_rag | 5 | 5.00 | 1.20 | 1308 |
| vector_rag | 5 | 5.00 | 1.20 | 1350 |

## Retrieval Speed

| Method | n | Mean | Median | P95 | Max |
|---|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.828s | 0.797s | 0.995s | 2.657s |
| reranked_rag | 50 | 0.901s | 0.459s | 0.789s | 20.853s |
| vector_rag | 50 | 0.373s | 0.212s | 0.404s | 7.267s |

## Retrieved Chunk Overlap

Average per-query Jaccard similarity between final retrieved chunk sets.

| Method | kg_rag | reranked_rag | vector_rag |
|---|---:|---:|---:|
| kg_rag | 1.00 | 0.23 | 0.66 |
| reranked_rag | 0.23 | 1.00 | 0.29 |
| vector_rag | 0.66 | 0.29 | 1.00 |

## Interpretation Notes

- Normalized final context size helps prevent one method from winning by sending more chunks.
- Chunk judgments expose whether a method retrieves useful context before answer quality is considered.
- Overlap helps show whether methods are genuinely retrieving different evidence.
- Bootstrap intervals are descriptive and depend on the available judged examples.
