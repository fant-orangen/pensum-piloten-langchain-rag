#!/usr/bin/env bash
# One-time setup: create a Python virtual environment on IDUN and install deps.
#
# Run this on the IDUN login node AFTER deploying the code with deploy.sh:
#   cd /cluster/work/$IDUN_USERNAME/pensum_piloten
#   bash idun/setup_env.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "==> Loading Python module ..."
module load Python/3.11.3-GCCcore-12.3.0

echo "==> Creating virtual environment ..."
python -m venv venv

echo "==> Activating venv and installing dependencies ..."
source venv/bin/activate
pip install --upgrade pip
pip install -e .

echo "==> Creating data directories ..."
mkdir -p data/chroma data/documents data/pgdata data/neo4j_data
mkdir -p idun/logs

echo "==> Pre-downloading HuggingFace embedding model ..."
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('intfloat/multilingual-e5-small')
print('Embedding model cached successfully.')
"

echo "==> Setup complete."
echo "    Next steps:"
echo "    1. Copy your documents into data/documents/"
echo "    2. Edit idun/.env.idun with your IDUN API key"
echo "    3. Build Apptainer containers:  bash idun/build_containers.sh"
echo "    4. Run ingestion:               sbatch idun/ingest.slurm"
echo "    5. Start the server:            sbatch idun/serve.slurm"
