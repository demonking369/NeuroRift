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

echo "[4/5] Starting NeuroRift agent runtime..."
neurorift run-agent --target "local-environment" --mode defensive

echo "[5/5] NeuroRift launch sequence complete."
