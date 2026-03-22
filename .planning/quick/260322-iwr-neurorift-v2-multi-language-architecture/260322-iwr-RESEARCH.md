# 260322-iwr RESEARCH.md
# Task: NeuroRift v2 Multi-Language Architecture Reconstruction
# Date: 2026-03-22

## 1. Existing Rust Infrastructure

The project already has a working Rust workspace at `core/`:
- `tokio` (full features) — async runtime
- `serde` / `serde_json` — JSON serialization (IPC protocol ready)
- `reqwest` — HTTP client
- `uuid`, `chrono`, `tracing`, `anyhow` — utilities

**Decision:** The new `recon/` Rust crate will be a **workspace member added to `core/Cargo.toml`**, not a separate workspace. This avoids duplicate toolchain compilation and allows sharing types.

---

## 2. Rust Recon Crate — Library Recommendations

### DNS Resolution
- **`hickory-resolver`** (formerly trust-dns-resolver) — async, tokio-native, supports all record types (A/AAAA/CNAME/MX/TXT/NS)
- Alternatives: `resolve` crate — lighter but less feature complete

### Subdomain Enumeration
- Custom: async DNS brute force using `hickory-resolver` + `tokio::task::JoinSet` for 10k concurrency
- Wordlist loaded via `tokio::fs::BufReader`

### Port Scanning
- **`tokio`** `TcpStream::connect` with timeout — fastest approach for TCP connect scan
- Raw SYN scan via `pnet` (libpnet) for stealth scanning — requires `CAP_NET_RAW`
- For banner grabbing: read first N bytes from connected stream

### HTTP Probing / Endpoint Fuzzing
- **`reqwest`** (already in workspace) for HTTP probing
- For max throughput fuzzing: use `tokio::sync::Semaphore` to bound concurrency (50k req/s target achievable on LAN)
- Tech detection: parse `Server`, `X-Powered-By`, `X-Framework` headers

### CLI Output
- All output: `serde_json::to_string()` to stdout
- Mode selection via `clap` crate (`--mode subdomain|port|fuzz|dns|probe`)

---

## 3. C Layer — Raw Socket Patterns

### Key Headers
```c
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <linux/if_packet.h>
```

### socket() call
```c
// AF_PACKET for raw layer 2 (full control)
int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
// or AF_INET for IP layer
int sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
```

### Build
- `gcc -O2 -o tcp_probe tcp_probe.c`
- Python calls via `subprocess.run([...], capture_output=True)` parsing stdout JSON

### Pitfall
- Raw sockets require `CAP_NET_RAW` — standard on Linux when running as root, else `setcap cap_net_raw+ep ./tcp_probe`

---

## 4. Assembly (NASM x86_64) — Shellcode Templates

### Linux x64 reverse shell pattern
```nasm
; Minimal 74-byte reverse shell skeleton
; Uses: socket(AF_INET,SOCK_STREAM,0), connect(), dup2(3x), execve(/bin/sh)
section .text
global _start
_start:
    ; setup sockaddr_in on stack
    ; syscall socket (41)
    ; syscall connect (42)
    ; syscall dup2 (33) × 3
    ; syscall execve (59)
```

### Build pipeline
```bash
nasm -f elf64 linux_x64_shell.asm -o shell.o
ld -o shell_elf shell.o
objcopy -O binary shell_elf shell.bin
# Extract hex bytes for Python poc_generator.py
python3 -c "print(open('shell.bin','rb').read().hex())"
```

### Python loading
```python
shellcode = bytes.fromhex(open("exploits/shellcode/linux_x64_shell.bin").read())
```

---

## 5. Python ↔ Language IPC Protocol

The user spec mandates all inter-language communication is **JSON over stdout**:

### subprocess pattern (Python → Rust/C)
```python
import subprocess, json

result = subprocess.run(
    ["./recon/target/release/recon", "--mode", "subdomain",
     "--target", domain, "--wordlist", "wordlist.txt"],
    capture_output=True, text=True, timeout=120
)
data = json.loads(result.stdout)
```

**Pitfalls:**
- Always set `timeout=` — hung processes block the pipeline
- Check `result.returncode` before parsing JSON
- Rust binary should print JSON to stdout and errors to stderr (don't mix)
- Use `--output json` flag pattern for clarity

### Bridge class pattern
```python
class ReconBridge:
    BINARY = Path("recon/target/release/recon")
    
    def run(self, mode: str, target: str, **kwargs) -> dict:
        cmd = [str(self.BINARY), "--mode", mode, "--target", target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"recon failed: {result.stderr}")
        return json.loads(result.stdout)
```

---

## 6. Makefile Architecture

```makefile
.PHONY: all rust c asm python test clean

all: rust c asm test

rust:
	cd core && cargo build --release

c:
	$(MAKE) -C network/

asm:
	bash exploits/shellcode/build_shellcode.sh

python:
	cd .. && .venv/bin/pytest tests/ -v

test: python

clean:
	cd core && cargo clean
	$(MAKE) -C network/ clean
```

---

## 7. Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Rust build times in dev | Use `cargo check` during dev, only `--release` in CI |
| Raw socket CAP_NET_RAW fails | Explicit error + fallback to Rust tokio TCP connect |
| ASM shellcode varies by kernel | Target only Linux 5.x+ kernel ABI, document requirement |
| 500-token context limit | `session/compressor.py` truncates to last 3 tool results + summary |
| llama.cpp down silently | `llama_client.py` checks `/health` endpoint, raises `LlamaServerError` |
| Scope enforcer bypassed | Enforcer is a decorator on every tool function, not optional middleware |

---

## 8. Build Order Confirmation

Follows user spec exactly:
1. Python foundation (ai/, scope/, session/, reporting/)
2. Rust recon engine (extend core/ workspace)
3. Tool layer (tools/ Python)
4. C network layer (network/)
5. ASM exploit layer (exploits/shellcode/)
6. Integration (main.py + full pipeline test)

## RESEARCH COMPLETE
File: .planning/quick/260322-iwr-neurorift-v2-multi-language-architecture/260322-iwr-RESEARCH.md
