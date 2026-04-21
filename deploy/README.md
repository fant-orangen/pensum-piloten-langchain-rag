# Deployment Runbook

Runs the full stack on your laptop and exposes it via a Cloudflare Quick Tunnel.
Zero cost beyond OpenAI tokens. Everything comes from `src/api/seed.py` —
users, courses, enrolments — so no manual provisioning.

## One-time setup

```bash
brew install --cask docker
brew install cloudflared
open -a Docker               # wait until Docker Desktop is running

cp deploy/.env.example .env  # then edit .env — set OPENAI_API_KEY and SECRET_KEY
docker compose build
```

## Test-day procedure

```bash
# 1. Start the stack. On first boot the API auto-runs seed.py (36 users, 3 courses).
docker compose up -d
docker compose logs -f api    # wait for "seed_complete" or "Application startup complete"; ^C

# 2. Build the knowledge graph into the container's Neo4j.
docker compose exec api ingest-kg

# 3. Smoke-test locally.
curl http://localhost:8080/health
open http://localhost:8080    # log in as g1u01@test.com / password123

# 4. Open the public tunnel. Prints a https://*.trycloudflare.com URL.
caffeinate -di &
cloudflared tunnel --url http://localhost:8080
```

Share the printed URL with participants. Credentials:

```
g1u01–g1u12@test.com   (KG-RAG course: os_g1)
g2u01–g2u12@test.com   (no-RAG course: os_g2)
g3u01–g3u12@test.com   (no-RAG course: os_g3)
admin@test.com / teacher@test.com   (for you)

Password for all: password123
```

## After the test

```bash
# Ctrl-C the cloudflared process.
./deploy/backup.sh      # backups/<timestamp>/{postgres,neo4j}.dump + chroma.tgz
docker compose down     # volumes preserved; data survives between runs
```

The Postgres dump contains every conversation and message from every
participant. Restore locally with `pg_restore` for analysis.

## Troubleshooting

- **Port 8080 in use** → edit `frontend.ports` in `docker-compose.yml`.
- **API logs show Neo4j connection refused** → wait ~20 s, healthcheck warming up.
- **OpenAI 429** → lower OpenAI model or raise your tier.
- **Tunnel URL changed mid-test** → quick tunnels don't survive `cloudflared`
  restart; keep that terminal open throughout the session.
