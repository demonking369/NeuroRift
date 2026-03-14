#!/bin/bash
# OpenClaw (NeuroRift Rust Core) — Docker Entrypoint
# Waits for the Python bridge (neurorift) to be healthy before starting.
set -e

BRIDGE_URL="${NEURORIFT_BRIDGE_URL:-http://neurorift:8766}"
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "⚡ OpenClaw (NeuroRift Core) — Entrypoint"
echo "🐍 Waiting for Python bridge at ${BRIDGE_URL}/health ..."

for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "${BRIDGE_URL}/health" > /dev/null 2>&1; then
        echo "✅ Python bridge ready (attempt ${i}/${MAX_RETRIES})"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "❌ Python bridge did not become ready after ${MAX_RETRIES} attempts. Starting anyway..."
    else
        echo "⏳ Waiting for bridge... (attempt ${i}/${MAX_RETRIES})"
        sleep "$RETRY_INTERVAL"
    fi
done

echo "🚀 Starting OpenClaw (neurorift-core)..."
exec /app/neurorift-core
