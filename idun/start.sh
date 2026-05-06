#!/usr/bin/env bash
# Orchestrate all services for the Pensum Piloten backend on IDUN.
# Called by serve.slurm — not intended to be submitted directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

COMPUTE_HOST="$(hostname)"

cleanup() {
    echo "==> Shutting down services ..."
    kill "$API_PID" 2>/dev/null || true
    apptainer instance stop neo4j_inst 2>/dev/null || true
    apptainer instance stop postgres_inst 2>/dev/null || true
    echo "==> All services stopped."
}
trap cleanup EXIT

echo "============================================="
echo " Pensum Piloten — IDUN Cluster Deployment"
echo " Host:  $COMPUTE_HOST"
echo " Date:  $(date)"
echo " Job:   ${SLURM_JOB_ID:-interactive}"
echo "============================================="

# ── Environment ──────────────────────────────────
module load Python/3.11.3-GCCcore-12.3.0
source venv/bin/activate
cp idun/.env.idun .env

# Load cluster identity variables
set -o allexport
# shellcheck source=idun/.env.idun
source idun/.env.idun
set +o allexport

# ── Data directories ─────────────────────────────
mkdir -p data/pgdata data/neo4j_data data/chroma idun/logs

# ── PostgreSQL ───────────────────────────────────
echo "==> Starting PostgreSQL ..."
apptainer instance start \
  --bind "$PROJECT_DIR/data/pgdata:/var/lib/postgresql/data" \
  idun/postgres.sif postgres_inst

echo "==> Waiting for PostgreSQL to become ready ..."
for i in $(seq 1 30); do
    if apptainer exec instance://postgres_inst pg_isready -q 2>/dev/null; then
        echo "    PostgreSQL ready after ${i}s"
        break
    fi
    sleep 1
done

# ── Neo4j ────────────────────────────────────────
echo "==> Starting Neo4j ..."
apptainer instance start \
  --bind "$PROJECT_DIR/data/neo4j_data:/data" \
  idun/neo4j.sif neo4j_inst

echo "==> Waiting for Neo4j to become ready ..."
for i in $(seq 1 30); do
    if python -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j','pensumpiloten')).verify_connectivity()" 2>/dev/null; then
        echo "    Neo4j ready after ${i}s"
        break
    fi
    sleep 1
done

# ── FastAPI backend ──────────────────────────────
echo "==> Starting FastAPI backend on port 8000 ..."
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# ── Connection info ──────────────────────────────
echo ""
echo "============================================="
echo " Services running on $COMPUTE_HOST"
echo "   API:  http://$COMPUTE_HOST:8000"
echo "   Health: http://$COMPUTE_HOST:8000/health"
echo ""
echo " To access from your local machine:"
echo "   ssh -L 8000:$COMPUTE_HOST:8000 ${IDUN_USERNAME}@${IDUN_LOGIN_NODE}"
echo "   Then call http://localhost:8000/health or point the frontend at http://localhost:8000."
echo "============================================="
echo ""

wait $API_PID
