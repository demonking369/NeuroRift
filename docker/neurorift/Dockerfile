# NeuroRift Python Bridge — Dockerfile
# Runs the FastAPI bridge server that connects OpenClaw (Rust) to Ollama
# and Python security tooling.

FROM python:3.11-slim AS base

# --- System dependencies ---
# curl: used in health checks and entrypoint wait loop
# nmap: required by python-nmap / scan module
# tor: dark web OSINT (Robin)
# build-essential / libssl-dev / pkg-config: native Python packages (cryptography etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        nmap \
        tor \
        build-essential \
        libssl-dev \
        pkg-config \
        git \
    && rm -rf /var/lib/apt/lists/*

# --- Python dependencies ---
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Application source ---
# Copy only what the bridge server needs
COPY modules/       ./modules/
COPY utils/         ./utils/
COPY prompts/       ./prompts/
COPY configs/       ./configs/
COPY ai_wrapper/    ./ai_wrapper/

# --- Entrypoint ---
COPY docker/neurorift/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --- Runtime metadata ---
EXPOSE 8766

# Data directory for sessions / audit / evolution (mounted as volume)
ENV NEURORIFT_HOME=/data/neurorift
RUN mkdir -p /data/neurorift

# Health check — the /health endpoint responds immediately on startup
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -sf http://localhost:8766/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
