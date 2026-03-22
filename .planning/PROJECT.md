# NeuroRift: llama.cpp Migration Milestone

## Overview
NeuroRift is an orchestrated multi-agent intelligence system for security research. This milestone focuses on migrating from Ollama to a local `llama.cpp` HTTP server to better leverage specialized hardware (RTX 2050 4GB VRAM) and achieve higher operational control.

## Core Value
High-performance, local-first AI orchestration for security tools with reduced dependency overhead.

## Requirements

### Validated
- ✓ Multi-agent orchestration (Planner, Operator, Analyst, Scribe)
- ✓ Security tool integration (Nmap, ProjectDiscovery)
- ✓ Web Dashboard (Next.js) & CLI
- ✓ Persistent session and artifact management
- ✓ Dockerized microservice architecture

### Active
- [ ] Replace Ollama with `llama.cpp` HTTP server (localhost:8080)
- [ ] Implement `llama_client.py` OpenAI-compatible wrapper
- [ ] Automate model download (Hermes-2-Pro-Mistral-7B-GGUF)
- [ ] Create `start_llama.sh` with optimized GPU offloading (n_gpu_layers 20)
- [ ] Update all modules and README for the new stack

### Out of Scope
- Migrating the web UI to a different framework
- Adding new security tools in this phase
- Changing the Rust execution engine logic

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| llama.cpp vs Ollama | Better VRAM management for RTX 2050 and finer control over n_gpu_layers | Active |
| OpenAI-compatible bridge | Enables easier integration with existing Langchain/Requests logic | Active |
| Hermes-2-Pro-Mistral-7B | Best-in-class tool calling capabilities for a 7B model | Active |

---
*Last updated: 2026-03-22 after initialization*
