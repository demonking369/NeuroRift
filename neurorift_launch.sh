#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${1:-}"
BOOT_PROMPT="You are NeuroRift, an autonomous cybersecurity agent. Boot in safe authorized mode, load skills, verify tools, and await tasking."

if ! command -v ollama >/dev/null 2>&1; then
  echo "❌ Ollama is not installed. Install it first: https://ollama.com/download"
  exit 1
fi

if ! command -v neurorift >/dev/null 2>&1; then
  echo "❌ neurorift command not found in PATH. Install package and wrapper first."
  exit 1
fi

if [ -z "$MODEL_NAME" ]; then
  MODEL_NAME="$(ollama list 2>/dev/null | awk 'NR==2{print $1}')"
fi

if [ -z "$MODEL_NAME" ]; then
  echo "❌ No local Ollama model found. Pull one first (example: ollama pull llama3)."
  exit 1
fi

echo "[1/5] Verifying runtime environment..."
python3 runtime_environment_check.py || true

echo "[2/5] Verifying model capabilities for $MODEL_NAME..."
CAP_JSON="$(python3 model_capability_check.py --model "$MODEL_NAME")"
echo "$CAP_JSON"
if ! echo "$CAP_JSON" | grep -q '"agent_ready": true'; then
  echo "❌ Model is not agent-ready. Aborting NeuroRift startup."
  exit 1
fi

echo "[3/5] Bootstrapping model session..."
ollama run "$MODEL_NAME" "$BOOT_PROMPT" >/dev/null || true

echo "[4/5] Starting NeuroRift agent runtime..."
neurorift run-agent --target "local-environment" --mode defensive

echo "[5/5] NeuroRift launch sequence complete."
