#!/usr/bin/env bash
# Build Apptainer (Singularity) container images for PostgreSQL and Neo4j.
#
# Run on the IDUN login node:
#   cd /cluster/work/<username>/pensum_piloten
#   bash idun/build_containers.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Building PostgreSQL container ..."
apptainer build --force postgres.sif postgres.def

echo "==> Building Neo4j container ..."
apptainer build --force neo4j.sif neo4j.def

echo "==> Containers built successfully:"
ls -lh *.sif
