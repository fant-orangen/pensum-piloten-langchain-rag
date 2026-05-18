# Retrieval Speed Analysis

Total retrieval records: 150

Fastest method by mean latency: `vector_rag` (0.390s).

## Summary By Method

| Method | n | Mean | Median | Std. dev. | Min | P25 | P75 | P95 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| kg_rag | 50 | 0.752s | 0.752s | 0.141s | 0.529s | 0.668s | 0.804s | 1.030s | 1.219s |
| reranked_rag | 50 | 0.504s | 0.368s | 0.755s | 0.329s | 0.351s | 0.397s | 0.678s | 5.690s |
| vector_rag | 50 | 0.390s | 0.208s | 1.175s | 0.166s | 0.199s | 0.227s | 0.395s | 8.526s |

## Notes

- Latency is measured by the review-generation script around retrieval only.
- Answer generation latency is intentionally excluded from this report.
- The join uses `query_id` plus anonymized `method_label`, because labels are shuffled per query.
