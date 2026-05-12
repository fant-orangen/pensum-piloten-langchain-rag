# Retrieval Speed Analysis

Total retrieval records: 150

Fastest method by mean latency: `vector_rag` (0.379s).

## Summary By Method

| Method | n | Mean | Median | Std. dev. | Min | P25 | P75 | P95 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.869s | 0.822s | 0.204s | 0.632s | 0.779s | 0.912s | 1.176s | 1.728s |
| reranked_rag | 50 | 0.596s | 0.459s | 0.644s | 0.327s | 0.404s | 0.606s | 0.781s | 4.954s |
| vector_rag | 50 | 0.379s | 0.205s | 0.977s | 0.171s | 0.196s | 0.268s | 0.392s | 7.107s |

## Notes

- Latency is measured by the review-generation script around retrieval only.
- Answer generation latency is intentionally excluded from this report.
- The join uses `query_id` plus anonymized `method_label`, because labels are shuffled per query.
