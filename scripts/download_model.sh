#!/usr/bin/env bash
# NeuroRift v2 — download_model.sh
# Downloads the recommended Hermes 2 Pro model for llama.cpp

set -euo pipefail
mkdir -p models
cd models

MODEL_URL="https://huggingface.co/NousResearch/Hermes-2-Pro-Mistral-7B-GGUF/resolve/main/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf"
MODEL_FILE="hermes-2-pro-mistral-7b.Q4_K_M.gguf"

if [ -f "$MODEL_FILE" ]; then
    echo "[*] Model already exists: models/$MODEL_FILE"
    exit 0
fi

echo "[*] Downloading $MODEL_FILE (~4.3GB)..."
wget -O "$MODEL_FILE" "$MODEL_URL" || curl -L -o "$MODEL_FILE" "$MODEL_URL"

echo "[OK] Model downloaded successfully."
