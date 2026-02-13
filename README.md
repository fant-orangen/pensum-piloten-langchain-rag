# Pensum Piloten (LangChain RAG)

## Graph-guided retrieval (KG2RAG-lite)

The project supports optional graph-guided retrieval:

1. Semantic seed retrieval from Chroma
2. Entity-overlap graph expansion (1-hop by default)
3. Optional cross-encoder reranking on expanded candidates

Enable in `.env`:

```env
GRAPH_ENABLED=true
GRAPH_HOPS=1
GRAPH_SEED_K=25
GRAPH_MAX_CANDIDATES=60
GRAPH_MIN_ENTITY_DF=2
GRAPH_MAX_ENTITY_DF=200
GRAPH_MAX_ENTITIES_PER_QUERY=30
GRAPH_INDEX_PATH=./data/graph/graph_index.json

RERANK_ENABLED=true
RERANK_FETCH_K=25
RERANK_TOP_K=5
RERANK_MODEL_NAME=cross-encoder/ms-marco-MiniLM-L-6-v2
```

Debug logs:

```env
GRAPH_LOG=true
GRAPH_LOG_TOP_N=8
GRAPH_LOG_PREVIEW_CHARS=120

RERANK_LOG=true
RERANK_LOG_TOP_N=8
RERANK_LOG_PREVIEW_CHARS=120
```

After changing graph settings, re-run ingestion so both Chroma and graph index are rebuilt:

```bash
python -m scripts.ingest
```
