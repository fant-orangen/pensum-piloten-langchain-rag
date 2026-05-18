# Retrieval Speed Analysis

Total retrieval records: 150

Fastest method by mean latency: `vector_rag` (0.385s).

## Summary By Method

| Method | n | Mean | Median | Std. dev. | Min | P25 | P75 | P95 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.834s | 0.798s | 0.211s | 0.639s | 0.747s | 0.879s | 0.994s | 2.063s |
| reranked_rag | 50 | 0.587s | 0.440s | 0.678s | 0.342s | 0.404s | 0.542s | 0.856s | 5.181s |
| vector_rag | 50 | 0.385s | 0.208s | 1.024s | 0.164s | 0.188s | 0.274s | 0.452s | 7.455s |

## Notes

- Latency is measured by the review-generation script around retrieval only.
- Answer generation latency is intentionally excluded from this report.
- The join uses `query_id` plus anonymized `method_label`, because labels are shuffled per query.
