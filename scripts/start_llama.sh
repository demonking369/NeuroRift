#!/usr/bin/env bash
# NeuroRift v2 — start_llama.sh
# Launch llama.cpp HTTP server with GPU offloading
set -euo pipefail

MODEL="${NEURORIFT_MODEL:-models/hermes-2-pro-mistral-7b.Q4_K_M.gguf}"
HOST="${NEURORIFT_HOST:-0.0.0.0}"
PORT="${NEURORIFT_PORT:-8080}"
GPU_LAYERS="${NEURORIFT_GPU_LAYERS:-20}"
CTX="${NEURORIFT_CTX:-4096}"
VENV="${NEURORIFT_VENV:-.venv}"

echo "[*] NeuroRift v2 — Starting llama.cpp server"
echo "    Model:       $MODEL"
echo "    Bind:        $HOST:$PORT"
echo "    GPU layers:  $GPU_LAYERS"
echo "    Context:     $CTX tokens"

if [ ! -f "$MODEL" ]; then
    echo "[!] Model not found: $MODEL"
    echo "    Run: bash scripts/download_model.sh"
    exit 1
fi

source "$VENV/bin/activate" 2>/dev/null || true

python -m llama_cpp.server \
    --model "$MODEL" \
    --n_gpu_layers "$GPU_LAYERS" \
    --n_ctx "$CTX" \
    --host "$HOST" \
    --port "$PORT"
