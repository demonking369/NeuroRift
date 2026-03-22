# Research: NeuroRift Migration to llama.cpp

## 1. llama.cpp Server Configuration
- **Library**: `llama-cpp-python[server]` is the preferred way to get an OpenAI-compatible API around `llama.cpp`.
- **API Endpoint**: `http://localhost:8080/v1/chat/completions`.
- **Model**: `Hermes-2-Pro-Mistral-7B-GGUF` (Q4_K_M) is ideal for 4GB VRAM.
- **Hardware Optimization (RTX 2050 4GB)**:
  - `n_gpu_layers`: 20 layers offloaded to GPU should fit comfortably within 4GB VRAM while leaving space for the KV cache.
  - `n_ctx`: 4096 is standard. Increasing this will consume more VRAM.
  - `host`: `0.0.0.0` for Docker/External access if needed, though `localhost` is safer for local-only security tools.

## 2. Tool Calling (Function Calling)
- **Model Support**: Hermes-2-Pro is specifically trained for tool calling using `<tool_call>` and `{"name": "...", "arguments": "..."}` syntax.
- **llama.cpp Support**: The server can pass through the tool definitions, but we must ensure the client (NeuroRift) correctly interprets the model's output format. Using an OpenAI-compatible client library (like `openai` or `httpx` with OAI schemas) simplifies this.

## 3. Integration Points
- **Primary Migration Target**: `ai_wrapper/llm_engine.py`.
- **Current Pattern**:
  - `httpx.post(".../api/generate")` -> Ollama specific format.
  - `requests.post(".../api/pull")` -> Ollama specific.
- **Target Pattern**:
  - Switch to OpenAI-compatible Chat Completions API.
  - Replace `num_ctx` and `options` with OpenAI-standard `max_tokens`, `temperature`, etc.

## 4. Implementation Pitfalls
- **Context Window**: Moving from Ollama's dynamic management to `llama.cpp`'s fixed `n_ctx` requires NeuroRift to handle truncation or notify the user when the context is full.
- **Dependency Conflict**: `ollama` python package should be removed to avoid confusion, but we must ensure no other module depends on its specific types.
- **Startup Sequence**: NeuroRift currently assumes Ollama is running (or tries to check it). The startup script `neurorift_launch.sh` will need updates to either start `llama.cpp` or check for it on port 8080.

## 5. Optimized Hardware Settings
- **n_batch**: 512 (default) is fine.
- **n_threads**: Match CPU cores (likely 8-12 for modern laptops).
- **GPU Layers**: If OOM occurs at 20, drop to 15. If VRAM usage is <3GB, attempt 25.
