# Roadmap: NeuroRift llama.cpp Migration

## Milestone 1: Engine Migration
Migrating the core AI inference engine from Ollama to a local llama.cpp server.

### Phase 1: Environment & Infrastructure [QUICK]
- **Goal:** Set up the model and server scripts.
- **Tasks:**
  - Create `download_model.sh` and fetch weights.
  - Create `start_llama.sh` and verify server boots on RTX 2050.
  - Install dependencies.

### Phase 2: Client Implementation [QUICK]
- **Goal:** Implement the OpenAI-compatible bridge.
- **Tasks:**
  - Create `ai_wrapper/llama_client.py`.
  - Implement tool-calling parser for Hermes-2-Pro.
  - Unit tests for the new client.

### Phase 3: Total Integration [QUICK]
- **Goal:** Replace all Ollama call sites.
- **Tasks:**
  - Refactor all `modules/` to use `LlamaClient`.
  - Remove `ollama` package and cleanup legacy configs.
  - Final end-to-end verification.

---
*Last updated: 2026-03-22*
