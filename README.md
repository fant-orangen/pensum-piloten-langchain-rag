# Pensum Piloten (LangChain RAG)

## Teaching modes (CLI)

When launching chat, you can pick among:

1. Socratic Tutor
2. Structured Direct Instructor
3. Active Recall Trainer

Start chat and choose interactively:

```bash
python -m scripts.chat
```

Or select directly:

```bash
python -m scripts.chat --mode socratic
python -m scripts.chat --mode structured_instructor
python -m scripts.chat --mode active_recall
```

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
GRAPH_ENTITY_EXTRACTOR=rule
GRAPH_SPACY_MODEL_NAME=en_core_web_sm
GRAPH_ADAPTIVE_ENABLED=false
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

## Retrieval Evaluation Harness

Run benchmark retrieval evaluation across four modes:

```bash
python -m scripts.eval_retrieval
```

Modes evaluated:

1. `baseline` (no graph, no rerank)
2. `rerank_only`
3. `graph_only`
4. `graph_rerank`

Outputs:

- dataset: `/Users/magnus/Documents/GitHub/BachelorTest/BachelorTest/pensum-piloten-langchain-rag/data/eval/retrieval_eval.jsonl`
- report: `/Users/magnus/Documents/GitHub/BachelorTest/BachelorTest/pensum-piloten-langchain-rag/data/eval/last_report.json`

Optional args:

```bash
python -m scripts.eval_retrieval --limit 10 --rank-cutoff 20
```

## Retrieval Debug Command

Inspect one query with compact diagnostics:

```bash
python -m scripts.debug_retrieval --query "What is virtual memory?" --mode graph_rerank
```

Mode options:

- `baseline`
- `rerank`
- `graph`
- `graph_rerank`

## Optional Output Grounding Check

Enable lightweight answer grounding verification:

```env
GROUNDING_ENABLED=true
GROUNDING_MODE=note    # or prune
GROUNDING_MIN_OVERLAP=0.18
```

- `note`: keep answer and append uncertainty note if unsupported segments are detected.
- `prune`: remove unsupported segments from the answer.
