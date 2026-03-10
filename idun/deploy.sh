#!/usr/bin/env bash
# Sync the project to the IDUN cluster work directory.
#
# Usage:
#   ./idun/deploy.sh
#
# Prerequisites:
#   - SSH access configured in idun/.env.idun (IDUN_USERNAME, IDUN_LOGIN_NODE)
#   - NTNU VPN if off-campus

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load IDUN_USERNAME and IDUN_LOGIN_NODE from the cluster env config
set -o allexport
# shellcheck source=idun/.env.idun
source "$SCRIPT_DIR/.env.idun"
set +o allexport

REMOTE="${IDUN_USERNAME}@${IDUN_LOGIN_NODE}"
REMOTE_DIR="/cluster/work/${IDUN_USERNAME}/pensum_piloten"

echo "==> Syncing project to $REMOTE:$REMOTE_DIR ..."

rsync -avz --progress \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.mypy_cache' \
  --exclude '.ruff_cache' \
  --exclude '.git' \
  --exclude 'data/chroma' \
  --exclude 'data/neo4j_data' \
  --exclude 'data/pgdata' \
  --exclude 'idun/*.sif' \
  "$(dirname "$SCRIPT_DIR")/" "$REMOTE:$REMOTE_DIR/"

echo "==> Done. SSH into IDUN and run the setup script:"
echo "    ssh $REMOTE"
echo "    cd $REMOTE_DIR"
echo "    bash idun/setup_env.sh"
