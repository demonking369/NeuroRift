# Requirements: llama.cpp Migration

## 1. Core Integration
- [ ] Install `llama-cpp-python[server]` on host system.
- [ ] Implement `ai_wrapper/llama_client.py`:
  - OpenAI-compatible chat completions interface.
  - Support for `tools` (function calling) via JSON schema.
  - Graceful context overflow handling (truncation or error reporting).
  - Default parameters: temp 0.1, max_tokens 4096.

## 2. Model Management
- [ ] Create `scripts/download_model.sh`:
  - Use `huggingface-cli` or `wget` to fetch `NousResearch/Hermes-2-Pro-Mistral-7B-GGUF`.
  - Target: `models/hermes-2-pro-mistral-7b.Q4_K_M.gguf`.

## 3. Server Orchestration
- [ ] Create `scripts/start_llama.sh`:
  - Launch `python -m llama_cpp.server`.
  - Config: `n_gpu_layers 20`, `n_ctx 4096`, port 8080.

## 4. Codebase Migration
- [ ] Audit `modules/` for any hardcoded Ollama endpoints or unique Ollama-client logic.
- [ ] Refactor `ai_wrapper/` to export the new `LlamaClient` as the primary interface.
- [ ] Update `requirements.txt` and `setup.py` (remove `ollama`, add `llama-cpp-python`).

## 5. Documentation
- [ ] Update `README.md` with new prerequisites and startup sequence.
- [ ] Update `DOCKER.md` (if relevant) to reflect local server dependency.
