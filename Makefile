# NeuroRift v2 — Root Makefile
# Builds all language components in the correct order:
# Python deps → Rust recon → C network → ASM shellcode → run tests

.PHONY: all rust c asm python test clean

all: rust c asm test

# ── Step 1: Python foundation (no build needed, just verify) ─────────────────
python:
	@echo "[PYTHON] Verifying Python foundation imports..."
	@. .venv/bin/activate && python -c "\
from scope.parser import parse_scope; \
from scope.enforcer import enforce_scope; \
from session.state import SessionState; \
from session.compressor import Compressor; \
from reporting.reporter import Reporter; \
from tools.shell_exec import ShellExecTool; \
print('[OK] Python foundation verified')"

# ── Step 2: Rust recon crate ─────────────────────────────────────────────────
rust:
	@echo "[RUST] Building recon engine..."
	@cd recon && cargo build --release 2>&1
	@echo "[OK] Rust recon built: recon/target/release/recon"

# ── Step 3: C network layer ──────────────────────────────────────────────────
c:
	@echo "[C] Building network modules..."
	@$(MAKE) -C network/
	@echo "[OK] C network layer built"

# ── Step 4: Assembly shellcode ───────────────────────────────────────────────
asm:
	@echo "[ASM] Compiling shellcode templates..."
	@bash exploits/shellcode/build_shellcode.sh || echo "[WARN] nasm not installed — shellcode not compiled"

# ── Tests ─────────────────────────────────────────────────────────────────────
test: python
	@echo "[TEST] Running test suite..."
	@. .venv/bin/activate && pytest tests/ -v 2>&1

# ── Verify cargo/rust check ────────────────────────────────────────────────
rust-check:
	@cd recon && cargo check 2>&1

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	@cd recon && cargo clean 2>/dev/null || true
	@$(MAKE) -C network/ clean 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "[OK] Clean complete"
