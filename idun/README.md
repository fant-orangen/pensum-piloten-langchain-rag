# IDUN HPC Cluster Deployment

Deploy the Pensum Piloten backend on the NTNU IDUN HPC cluster with the
Kimi K2.5 LLM provided via the IDUN LLM gateway.

## Prerequisites

- SSH access to IDUN (`idun-login1.hpc.ntnu.no` or `idun-login2.hpc.ntnu.no`)
- An IDUN LLM API key (request from help@hpc.ntnu.no)
- NTNU VPN if working off-campus

## Configuration

All user-specific settings live in `idun/.env.idun`. Edit this file before
running any of the scripts below. The key fields to set are:

```
IDUN_USERNAME=<your-ntnu-username>
IDUN_LOGIN_NODE=idun-login2.hpc.ntnu.no   # or idun-login1
IDUN_API_KEY=<your-idun-llm-api-key>
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
```

## Quick Start

### 1. Deploy code to the cluster

From your **local machine**, in the project root:

```bash
./idun/deploy.sh
```

This rsyncs the project to `/cluster/work/$IDUN_USERNAME/pensum_piloten`.
You will be prompted for your NTNU password (or it will use your SSH key
if you have one configured — see SSH Keys section below).

### 2. Set up the environment (one-time)

SSH into IDUN and run the setup script:

```bash
ssh $IDUN_USERNAME@$IDUN_LOGIN_NODE
cd /cluster/work/$IDUN_USERNAME/pensum_piloten
bash idun/setup_env.sh
```

### 3. Find your Slurm account and update the scripts

```bash
sacctmgr show assoc format=Account%15,User,QOS | grep $USER
```

Edit `idun/serve.slurm` and `idun/ingest.slurm` and replace
`share-ie-idi` with the account name from the output above.
If you see a `share-*` account, prefer that one (higher priority).

### 4. Build database containers (one-time)

```bash
bash idun/build_containers.sh
```

### 5. Copy documents and run ingestion

```bash
# Copy your course documents
cp /path/to/documents/* data/documents/

# Submit the ingestion job
sbatch idun/ingest.slurm
# Monitor: tail -f idun/logs/ingest_<jobid>.log
```

### 6. Start the server

```bash
sbatch idun/serve.slurm
```

Check which compute node was assigned:

```bash
squeue -u $USER
# Note the NODELIST column, e.g. "idun-04-01"
```

## SSH Keys (Recommended)

Without an SSH key you will be prompted for your NTNU password on every
`ssh` or `rsync` command. Setting up a key pair eliminates this.

**Step 1 — Generate a key pair on your local machine** (skip if you already
have one at `~/.ssh/id_ed25519`):

```bash
ssh-keygen -t ed25519 -C "IDUN access"
```

This creates two files:
- `~/.ssh/id_ed25519` — your **private key** (never share this)
- `~/.ssh/id_ed25519.pub` — your **public key** (safe to share)

**Step 2 — Copy the public key to IDUN:**

```bash
ssh-copy-id $IDUN_USERNAME@$IDUN_LOGIN_NODE
```

You will be asked for your NTNU password one final time. After this,
SSH reads your private key silently and the password prompt disappears
for all future connections.

**How it works:** IDUN stores your public key in `~/.ssh/authorized_keys`.
When you connect, your local machine proves it holds the matching private
key via a cryptographic challenge — no password needed.

## Accessing the Services

### Development / Testing: SSH Tunnel

Once the server job is running, find the compute node name:

```bash
squeue -u $USER   # e.g. NODELIST = idun-04-01
```

Then from your **local machine**, open an SSH tunnel through the login node:

```bash
ssh -L 8000:<compute-node>:8000 -L 7860:<compute-node>:7860 \
  $IDUN_USERNAME@$IDUN_LOGIN_NODE
```

Open http://localhost:7860 in your browser.
The start.sh log will also print this exact command when the job starts.

### Production: External Access for Students

IDUN compute nodes do not have public IPs. For student-facing access,
coordinate with the HPC team (help@hpc.ntnu.no) about:

- A reverse proxy endpoint for the application
- A persistent service allocation
- Their recommended approach for web applications on IDUN

The HPC team already runs externally accessible services (Open WebUI,
LibreChat) and can advise on the best approach.

## File Overview

| File                  | Purpose                                          |
| --------------------- | ------------------------------------------------ |
| `.env.idun`           | All cluster-specific config (username, keys etc) |
| `deploy.sh`           | Rsync project from local machine to IDUN         |
| `setup_env.sh`        | One-time Python venv and dependency setup        |
| `build_containers.sh` | Build Apptainer images for PostgreSQL and Neo4j  |
| `serve.slurm`         | Slurm job: start all services (API + UI + DBs)   |
| `ingest.slurm`        | Slurm job: run document ingestion pipeline       |
| `start.sh`            | Orchestration script called by serve.slurm       |
| `postgres.def`        | Apptainer definition for PostgreSQL 16           |
| `neo4j.def`           | Apptainer definition for Neo4j 5 Community       |

## Monitoring

```bash
# Check job status
squeue -u $USER

# View server logs
tail -f idun/logs/serve_<jobid>.log

# Check API health (from within cluster or via SSH tunnel)
curl http://<compute-node>:8000/health

# Cancel a running job
scancel <jobid>
```

## Troubleshooting

- **"module: command not found"**: Make sure you're on the login node or
  inside a Slurm job, not on your local machine.
- **Neo4j/PostgreSQL won't start**: Check that `data/pgdata` and
  `data/neo4j_data` are writable. Try deleting them for a fresh start.
- **LLM API errors**: Verify you're on NTNU network/VPN and that
  `IDUN_API_KEY` in `.env.idun` is correct. Test with:
  `curl https://llm.hpc.ntnu.no/v1/models -H "Authorization: Bearer $IDUN_API_KEY"`
- **Container build fails**: Apptainer needs network access to pull Docker
  images. Build on the login node, not inside a Slurm job.
