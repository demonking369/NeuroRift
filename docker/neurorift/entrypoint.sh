#!/bin/bash
# NeuroRift Python Bridge — Docker Entrypoint
# Waits for llama.cpp to be ready before starting the bridge server.
set -e

LLAMA_HOST="${LLAMA_HOST:-http://ollama:8080}"
MAX_RETRIES=60
RETRY_INTERVAL=2

echo "🧠 NeuroRift Python Bridge — Entrypoint"
echo "📡 Waiting for llama.cpp at ${LLAMA_HOST} ..."

for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "${LLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo "✅ llama.cpp is ready (attempt ${i}/${MAX_RETRIES})"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "❌ llama.cpp did not become ready after ${MAX_RETRIES} attempts. Starting anyway..."
    else
        echo "⏳ Waiting for llama.cpp... (attempt ${i}/${MAX_RETRIES})"
        sleep "$RETRY_INTERVAL"
    fi
done

echo "🚀 Starting NeuroRift Python Bridge..."
exec uvicorn modules.web.bridge_server:app \
    --host "${BRIDGE_HOST:-0.0.0.0}" \
    --port "${BRIDGE_PORT:-8766}" \
    --log-level "${LOG_LEVEL:-info}" \
    --forwarded-allow-ips='*'
