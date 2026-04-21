#!/usr/bin/env bash
# Dump all persistent state from the running docker compose stack into
# backups/<timestamp>/{postgres.dump,neo4j.dump,chroma.tgz}.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TS="$(date +%Y%m%dT%H%M%S)"
OUT="backups/${TS}"
mkdir -p "$OUT"

set -a
# shellcheck disable=SC1091
source .env
set +a

echo "→ Postgres dump"
docker compose exec -T postgres pg_dump \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-pensum_piloten}" \
    -F c -f /tmp/pensum.dump
docker compose cp "postgres:/tmp/pensum.dump" "${OUT}/postgres.dump"
docker compose exec -T postgres rm /tmp/pensum.dump

echo "→ Neo4j dump (stopping DB briefly)"
docker compose exec -T neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-pensumpiloten}" \
    "STOP DATABASE neo4j WAIT" >/dev/null
docker compose exec -T neo4j neo4j-admin database dump neo4j \
    --to-path=/tmp --overwrite-destination=true
docker compose cp "neo4j:/tmp/neo4j.dump" "${OUT}/neo4j.dump"
docker compose exec -T neo4j rm /tmp/neo4j.dump
docker compose exec -T neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-pensumpiloten}" \
    "START DATABASE neo4j WAIT" >/dev/null

echo "→ Chroma tarball"
tar czf "${OUT}/chroma.tgz" -C data chroma

docker compose ps > "${OUT}/env.txt"

echo "✓ Done: ${OUT}"
ls -lh "${OUT}"
