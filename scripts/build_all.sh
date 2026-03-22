#!/usr/bin/env bash
# NeuroRift v2 — build_all.sh
# Invokes the root Makefile to build Rust, C, and ASM components

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[*] NeuroRift v2 — Building all multi-language components"
make all
echo "[OK] Build complete"
