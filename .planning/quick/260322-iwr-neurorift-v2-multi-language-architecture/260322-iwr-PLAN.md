---
quick_id: 260322-iwr
task: NeuroRift v2 Multi-Language Architecture Reconstruction
date: 2026-03-22
mode: quick-full
must_haves:
  truths:
    - All 6 build steps scaffolded as working, compilable files
    - Python AI foundation (ai/, scope/, session/, reporting/) fully implemented
    - Rust recon crate added to core/ workspace with the 5 modules
    - Tool layer (Python) with scope enforcer integrated on every tool
    - C network layer (3 C sources + Makefile)
    - Assembly shellcode templates + build script
    - main.py wires everything together
    - Makefile builds all languages in correct order
    - Full pytest suite passes
  artifacts:
    - recon/ Rust crate (subdomain_enum, port_scanner, endpoint_fuzzer, dns_resolver, http_prober)
    - recon/recon_bridge.py Python subprocess wrapper
    - network/ C directory (raw_socket.c, packet_crafter.c, tcp_probe.c + Makefile)
    - exploits/shellcode/ ASM directory (linux_x64_shell.asm, linux_x64_exec.asm, rop_gadgets.asm, build_shellcode.sh)
    - ai/llama_client.py, ai/planner.py, ai/executor.py
    - scope/parser.py, scope/enforcer.py
    - session/state.py, session/compressor.py
    - reporting/reporter.py
    - tools/ (sqli, xss, idor, ssrf, ssti, xxe, open_redirect, auth_bypass, race_condition, shell_exec)
    - main.py, config.yaml, Makefile, Cargo.toml (updated)
    - scripts/ (start_llama.sh, download_model.sh, build_all.sh, install_deps.sh)
---

# NeuroRift v2 — Multi-Language Architecture Reconstruction Plan

## Overview

Reconstruct NeuroRift into a 5-language system (Python + Rust + C + ASM + Bash). All languages communicate via JSON over subprocess. Python is the orchestration spine. Rust handles all network-heavy recon. C handles raw kernel-level packets. ASM provides shellcode templates. Bash handles build and environment tasks.

---

## Task 1: Python Foundation Layer

**Files:**
- `ai/__init__.py`, `ai/llama_client.py`, `ai/planner.py`, `ai/executor.py`
- `ai/prompts/planner_system.txt`, `ai/prompts/executor_system.txt`
- `scope/__init__.py`, `scope/parser.py`, `scope/enforcer.py`
- `session/__init__.py`, `session/state.py`, `session/compressor.py`
- `reporting/__init__.py`, `reporting/reporter.py`
- `config.yaml`
- `requirements.txt` (updated)

**Action:**
1. Create `ai/llama_client.py` — OpenAI-compatible httpx client for localhost:8080/v1/chat/completions with tool calling, context overflow handling, health check (`LlamaServerError` if down)
2. Create `ai/planner.py` — receives compressed recon JSON, outputs ordered attack plan, max 500 token input enforced
3. Create `ai/executor.py` — dispatches tool calls, feeds results back to model, handles stop conditions
4. Create `ai/prompts/planner_system.txt` and `executor_system.txt` with role, constraints, JSON output schema
5. Create `scope/parser.py` — normalizes H1 markdown tables, Bugcrowd JSON, plain domain list, wildcards, IP ranges into `ScopeMap` dataclass
6. Create `scope/enforcer.py` — `@enforce_scope` decorator, runs before every tool call, validates domain/wildcard/URL encoding bypass
7. Create `session/state.py` — persists all findings to disk (JSON), resumable
8. Create `session/compressor.py` — truncates to last 3 tool results + running summary, hard cap 500 tokens
9. Create `reporting/reporter.py` — HackerOne-ready markdown: title, CVSS, steps_to_reproduce, impact, remediation, evidence
10. Create `config.yaml` — llama.cpp host, ports, model, timeouts, session dir

**Verify:** `python -c "from ai.llama_client import LlamaClient; from scope.enforcer import enforce_scope; from session.state import SessionState; from reporting.reporter import Reporter; print('imports OK')"` succeeds

**Done:** Python foundation importable and tested

---

## Task 2: Rust Recon Engine

**Files:**
- `core/Cargo.toml` — add `recon` workspace member
- `recon/Cargo.toml`
- `recon/src/main.rs` — CLI entry, `--mode` dispatch, JSON stdout
- `recon/src/subdomain_enum.rs` — async DNS brute force, tokio JoinSet, 10k concurrency
- `recon/src/port_scanner.rs` — tokio TCP connect scan with timeout, banner grab
- `recon/src/endpoint_fuzzer.rs` — HTTP path brute force, semaphore-bounded concurrency
- `recon/src/dns_resolver.rs` — hickory-resolver bulk DNS A/AAAA/CNAME/MX/TXT/NS
- `recon/src/http_prober.rs` — reqwest HTTP/S probing, header tech detection
- `recon/recon_bridge.py` — Python subprocess wrapper

**Action:**
1. Add `"recon"` to `core/Cargo.toml` workspace members
2. Create `recon/Cargo.toml` with deps: `tokio` (full), `serde`/`serde_json`, `clap` (derive), `hickory-resolver`, `reqwest`, `anyhow`
3. Implement `recon/src/main.rs` — clap CLI: `--mode`, `--target`, `--wordlist`, `--output json`; dispatch to modules; serialize output to stdout as JSON
4. Implement `subdomain_enum.rs` — load wordlist lines, spawn async DNS A-record lookups via `JoinSet`, collect live subdomains
5. Implement `port_scanner.rs` — tokio `TcpStream::connect_timeout`, 65535 port sweep, banner grab first 256 bytes
6. Implement `endpoint_fuzzer.rs` — reqwest GET with semaphore, filter 200/301/302/403, output live endpoints
7. Implement `dns_resolver.rs` — hickory-resolver async resolve for each record type, collect into HashMap
8. Implement `http_prober.rs` — reqwest HEAD+GET, extract Server/X-Powered-By/X-Framework headers as tech fingerprint
9. Create `recon/recon_bridge.py` — `ReconBridge` class with `run(mode, target, **kwargs) -> dict`, handles timeout and returncode

**Verify:**
- `cd core && cargo check 2>&1 | grep -E "^error"` — zero errors
- `python -c "from recon.recon_bridge import ReconBridge; print('bridge OK')"` succeeds

**Done:** Rust recon crate compiles cleanly; Python bridge importable

---

## Task 3: Python Tool Layer

**Files:**
- `tools/__init__.py`
- `tools/sqli.py`, `tools/xss.py`, `tools/idor.py`, `tools/ssrf.py`
- `tools/ssti.py`, `tools/xxe.py`, `tools/open_redirect.py`
- `tools/auth_bypass.py`, `tools/race_condition.py`, `tools/shell_exec.py`

**Action:**
1. Create base pattern in `tools/__init__.py` with `@enforce_scope` import and `ToolResult` dataclass
2. Implement each tool as a class with:
   - `schema()` classmethod returning JSON Schema draft-07 for AI tool calling
   - `run(target, **kwargs) -> ToolResult` method
   - Scope enforcer check at top of every `run()`
3. `sqli.py` — sqlmap integration + custom error/blind/time payloads, returns structured findings
4. `xss.py` — reflected/stored/DOM payloads, encoding variants
5. `idor.py` — ID parameter enumeration, auth context switching via session cookie swap
6. `ssrf.py` — internal network probing, OOB via callback URL (Burp Collaborator placeholder)
7. `ssti.py` — Jinja2/Twig/Freemarker detection, RCE confirmation payloads
8. `xxe.py` — file read, SSRF via XXE, OOB detection
9. `open_redirect.py` — redirect chain detection, SSRF escalation check
10. `auth_bypass.py` — JWT alg:none, session fixation check
11. `race_condition.py` — concurrent request engine (uses Rust http_prober via bridge)
12. `shell_exec.py` — **strict whitelist only**: `['nmap','subfinder','ffuf','nuclei','whatweb','sqlmap','curl','dig','nslookup','whois']`, timeout=60s, no rm/dd/format ever

**Verify:** `python -c "from tools.sqli import SQLiTool; from tools.shell_exec import ShellExecTool; print(ShellExecTool.schema())"` succeeds

**Done:** All 10 tool modules importable with correct schema

---

## Task 4: C Network Layer

**Files:**
- `network/Makefile`
- `network/raw_socket.c` + `network/raw_socket.h`
- `network/packet_crafter.c`
- `network/tcp_probe.c`
- `network/network_bridge.py`

**Action:**
1. Create `network/raw_socket.c` — `create_raw_socket()` using `socket(AF_INET, SOCK_RAW, IPPROTO_TCP)`, error handling, JSON status output on stdout
2. Create `network/packet_crafter.c` — `craft_tcp_syn()` building manual IP+TCP headers, checksum calculation, `sendto()`. Takes `--target IP --port PORT`, outputs JSON `{sent: true, ttl: N}`
3. Create `network/tcp_probe.c` — full SYN/ACK cycle detection: send SYN, detect SYN-ACK (open) vs RST (closed) vs timeout (filtered), JSON output `{host, port, state}`
4. Create `network/Makefile` — `gcc -O2 -o raw_socket raw_socket.c`, `gcc -O2 -o packet_crafter packet_crafter.c`, `gcc -O2 -o tcp_probe tcp_probe.c`, `all:` target
5. Create `network/network_bridge.py` — `NetworkBridge` class, subprocess to compiled C binaries, parses JSON output

**Verify:** `make -C network/ 2>&1 | grep -E "^error"` — zero errors

**Done:** C network layer compiles; bridge importable

---

## Task 5: Assembly Exploit Layer

**Files:**
- `exploits/__init__.py`
- `exploits/shellcode/linux_x64_shell.asm` — x86_64 reverse shell
- `exploits/shellcode/linux_x64_exec.asm` — execve shellcode
- `exploits/shellcode/rop_gadgets.asm` — ROP chain templates
- `exploits/shellcode/build_shellcode.sh` — nasm + objcopy pipeline
- `exploits/poc_generator.py` — loads compiled shellcode, generates PoC scripts
- `exploits/exploit_bridge.py` — AI-callable interface

**Action:**
1. Write `linux_x64_shell.asm` — complete x86_64 Linux reverse shell (socket→connect→dup2×3→execve /bin/sh), XOR encoded
2. Write `linux_x64_exec.asm` — execve shellcode (`/bin/sh -c cmd`)
3. Write `rop_gadgets.asm` — commented ROP gadget stubs for NX-bypass PoC demonstration
4. Write `build_shellcode.sh` — `nasm -f elf64 *.asm`, `ld`, `objcopy -O binary`, hex extraction
5. Write `exploits/poc_generator.py` — `PoCGenerator` class: loads `shellcode/*.bin`, generates Python/C PoC file for buffer overflow / format string / UAF findings
6. Write `exploits/exploit_bridge.py` — `ExploitBridge.generate_poc(vuln_type, target_info) -> str` — AI calls this for confirmed vulns, selects correct shellcode template

**Verify:** `bash exploits/shellcode/build_shellcode.sh 2>&1` — nasm compiles (or controlled fail if nasm not installed with clear message)

**Done:** ASM shellcode templates in place; PoC generator importable

---

## Task 6: Full Integration & main.py

**Files:**
- `main.py` — top-level entry point
- `Makefile` — root build orchestration
- `scripts/start_llama.sh`, `scripts/download_model.sh`, `scripts/build_all.sh`, `scripts/install_deps.sh`
- `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- Updated `tests/` with new integration test

**Action:**
1. Create `main.py`:
   - argparse: `--scope scope.txt --target URL --output-dir DIR --resume SESSION_ID`
   - Load config.yaml
   - Check llama.cpp health (fail hard with clear message if down)
   - Parse scope via `scope/parser.py`
   - Initialize session via `session/state.py`
   - Run orchestration loop: `ai/planner.py` → `ai/executor.py` → tools → compress → repeat
   - Generate report via `reporting/reporter.py`
2. Create root `Makefile` with targets: `all`, `rust`, `c`, `asm`, `test`, `clean`
3. Write `scripts/start_llama.sh`, `scripts/download_model.sh`, `scripts/build_all.sh`, `scripts/install_deps.sh`
4. Write `tests/integration/test_full_pipeline.py` — mock llama.cpp, mock scope, run main loop end-to-end, assert findings saved to disk
5. Run `pytest tests/ -v` — all tests pass

**Verify:**
- `python main.py --help` exits 0
- `pytest tests/ -v` shows all tests passing
- `make --dry-run` shows correct build sequence

**Done:** Full pipeline integrates; all tests pass; `python main.py --help` works
