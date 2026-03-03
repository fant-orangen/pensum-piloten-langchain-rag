#!/bin/bash
#SBATCH --job-name=pensum-piloten
#SBATCH --account=share-ie-idi
#SBATCH --partition=CPUQ
#SBATCH --time=7-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=idun/logs/serve_%j.log

# ── Resolve project directory from the script location ──
WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$WORKDIR"

exec bash idun/start.sh
