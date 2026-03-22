#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${1:-}"
BOOT_PROMPT="You are NeuroRift, an autonomous cybersecurity agent. Boot in safe authorized mode, load skills, verify tools, and await tasking."

# Handled by requirements.txt now

if ! command -v neurorift >/dev/null 2>&1; then
  echo "❌ neurorift command not found in PATH. Install package and wrapper first."
  exit 1
fi

if [ -z "$MODEL_NAME" ]; then
  MODEL_NAME="hermes-2-pro-mistral-7b"
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
python3 -c "import asyncio; from ai_wrapper.llama_client import LlamaClient; asyncio.run(LlamaClient().generate_chat([{'role': 'user', 'content': '$BOOT_PROMPT'}], model='$MODEL_NAME'))" >/dev/null || true

echo "[4/5] Starting NeuroRift agent runtime..."
neurorift run-agent --target "local-environment" --mode defensive

echo "[5/5] NeuroRift launch sequence complete."
