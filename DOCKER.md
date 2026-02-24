# NeuroRift × OpenClaw — Docker Guide

## Quick Start (Production)

```bash
# 1. Clone and enter the repo
git clone https://github.com/demonking369/NeuroRift && cd NeuroRift

# 2. Create your environment file
cp .env.example .env

# 3. Build and start all services
docker compose up --build

# 4. Pull an AI model (first time only — do this in a new terminal while containers start)
docker compose exec ollama ollama pull llama3

# 5. Open the web UI
open http://localhost:3000
```

---

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Host machine                                               │
│                                                             │
│  Browser ──→ http://localhost:3000                          │
│              │                                              │
│      ┌───────▼──────┐     Docker network: neurorift_net    │
│      │   web-ui     │ (Next.js, port 3000)                 │
│      │   Node 20    │                                       │
│      └────┬─────────┘                                       │
│           │ /api/bridge/*  →  http://neurorift:8766         │
│           │ /api/ws/*      →  http://openclaw:8765          │
│      ┌────▼─────────┐   ┌─────────────────────┐            │
│      │  openclaw    │   │     neurorift        │            │
│      │  Rust Core   │──▶│  Python FastAPI      │            │
│      │  WS :8765    │   │  Bridge :8766        │            │
│      └──────────────┘   └──────────┬──────────┘            │
│                                    │                        │
│                          ┌─────────▼──────────┐            │
│                          │      ollama         │            │
│                          │  AI Model Server    │            │
│                          │  :11434 (internal)  │            │
│                          └─────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Development Mode (Hot Reload)

```bash
# Source code is mounted as volumes — edit files and see changes instantly
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Development differences from production:
| Feature | Production | Development |
|---|---|---|
| Python bridge | `uvicorn` (stable) | `uvicorn --reload` |
| Next.js | `next start` (standalone) | `next dev` |
| Source code | Baked into image | Volume-mounted |
| Ollama port | Internal only | `127.0.0.1:11434` exposed |
| Debug ports | Not exposed | Bridge/Openclaw on `127.0.0.1` |

---

## Volumes

| Volume | Container path | Purpose |
|---|---|---|
| `ollama_models` | `/root/.ollama` | Ollama model files |
| `neurorift_sessions` | `/data/neurorift/sessions` | Session state JSON |
| `neurorift_audit` | `/data/neurorift/audit` | Audit logs |
| `neurorift_evolution` | `/data/neurorift/evolution` | Evolution/mutation data |

Sessions persist across `docker compose restart` and `down`/`up` cycles.

> [!WARNING]
> `docker compose down -v` will **delete all volumes** including sessions. Use `docker compose down` (without `-v`) for safe shutdown.

---

## GPU Support (NVIDIA)

1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment the `deploy` block in `docker-compose.yml` under the `ollama` service:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: all
             capabilities: [gpu]
   ```
3. Restart: `docker compose up --build`

---

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MAIN_MODEL` | `llama3` | Primary AI model |
| `OLLAMA_ASSISTANT_MODEL` | `llama3` | Chat assistant model |
| `AI_ENABLED` | `true` | Enable/disable AI features |
| `WEB_UI_PORT` | `3000` | Host port for the web UI |
| `LOG_LEVEL` | `info` | Python bridge log level |
| `RUST_LOG` | `info` | Rust core log level |
| `OPENAI_API_KEY` | *(blank)* | Optional OpenAI key |
| `ANTHROPIC_API_KEY` | *(blank)* | Optional Anthropic key |
| `GOOGLE_API_KEY` | *(blank)* | Optional Google key |

---

## Pre-Pulling Models

```bash
# Pull default model (recommended)
docker compose exec ollama ollama pull llama3

# Pull a smaller/faster model
docker compose exec ollama ollama pull llama3.2

# List available models
docker compose exec ollama ollama list
```

---

## Common Commands

```bash
# Start in background
docker compose up -d

# View logs for all services
docker compose logs -f

# View logs for one service
docker compose logs -f neurorift

# Restart a single service
docker compose restart web-ui

# Stop everything (keeps volumes)
docker compose down

# Stop and remove volumes (⚠️ deletes sessions)
docker compose down -v

# Rebuild a specific service
docker compose build neurorift && docker compose up -d neurorift

# Open a shell in the Python bridge container
docker compose exec neurorift bash

# Check all container health states
docker compose ps
```

---

## Troubleshooting

### Containers keep restarting

```bash
docker compose logs openclaw   # check for bridge connection errors
docker compose logs neurorift  # check for Ollama connectivity
```

Startup dependency order: `ollama` → `neurorift` → `openclaw` → `web-ui`
Each service waits for the previous to be healthy.

### Ollama model not found

```bash
docker compose exec ollama ollama pull llama3
```

### Port 3000 already in use

Change `WEB_UI_PORT` in your `.env`:
```
WEB_UI_PORT=3001
```

### Sessions lost after restart

Ensure you used `docker compose down` **without** `-v`. Check volumes:
```bash
docker volume ls | grep neurorift
docker volume inspect neurorift_neurorift_sessions
```
