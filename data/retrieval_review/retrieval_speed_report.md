# Retrieval Speed Analysis

Total retrieval records: 150

Fastest method by mean latency: `vector_rag` (0.373s).

## Summary By Method

| Method | n | Mean | Median | Std. dev. | Min | P25 | P75 | P95 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.828s | 0.797s | 0.285s | 0.525s | 0.731s | 0.852s | 0.995s | 2.657s |
| reranked_rag | 50 | 0.901s | 0.459s | 2.884s | 0.284s | 0.375s | 0.564s | 0.789s | 20.853s |
| vector_rag | 50 | 0.373s | 0.212s | 0.998s | 0.146s | 0.173s | 0.258s | 0.404s | 7.267s |

## Notes

- Latency is measured by the review-generation script around retrieval only.
- Answer generation latency is intentionally excluded from this report.
- The join uses `query_id` plus anonymized `method_label`, because labels are shuffled per query.
