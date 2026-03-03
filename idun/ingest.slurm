#!/bin/bash
#SBATCH --job-name=pensum-ingest
#SBATCH --account=share-ie-idi
#SBATCH --partition=CPUQ
#SBATCH --time=0-04:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=idun/logs/ingest_%j.log

# ── Resolve project directory from the script location ──
WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$WORKDIR"

echo "==> Starting ingestion on $(hostname) at $(date)"

# ── Environment ──
module load Python/3.11.3-GCCcore-12.3.0
source venv/bin/activate
cp idun/.env.idun .env

# ── Data directories ──
mkdir -p data/neo4j_data

# ── Start Neo4j (required for KG ingestion) ──
echo "==> Starting Neo4j ..."
apptainer instance start \
  --bind "$WORKDIR/data/neo4j_data:/data" \
  idun/neo4j.sif neo4j_inst

echo "==> Waiting for Neo4j to become ready ..."
for i in $(seq 1 30); do
    if python -c "from neo4j import GraphDatabase; GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j','pensumpiloten')).verify_connectivity()" 2>/dev/null; then
        echo "    Neo4j ready after ${i}s"
        break
    fi
    sleep 1
done

# ── Run KG ingestion ──
echo "==> Running KG ingestion ..."
python -m scripts.ingest_kg

# ── Cleanup ──
echo "==> Stopping Neo4j ..."
apptainer instance stop neo4j_inst

echo "==> Ingestion finished at $(date)"
