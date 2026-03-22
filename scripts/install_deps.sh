#!/usr/bin/env bash
# NeuroRift v2 — install_deps.sh
# Install required system packages, Rust, and Python dependencies

set -euo pipefail

echo "[*] NeuroRift v2 — Installing dependencies"

if command -v apt-get &>/dev/null; then
    echo "[*] Installing system packages via apt..."
    sudo apt-get update
    sudo apt-get install -y build-essential gcc make nasm binutils nmap curl dnsutils whois
fi

if ! command -v cargo &>/dev/null; then
    echo "[*] Installing Rust toolchain..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo "[*] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install llama-cpp-python[server]

echo "[OK] Dependencies installed successfully. Run 'make all' next."
