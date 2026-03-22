---
quick_id: 260322-hnv
title: Replace Ollama with llama.cpp
date: 2026-03-22
must_haves:
  truths:
    - llama.cpp server runs on port 8080
    - llama_client.py provides OpenAI-compatible interface
    - GPU offloading is optimized for RTX 2050
  artifacts:
    - scripts/download_model.sh
    - scripts/start_llama.sh
    - ai_wrapper/llama_client.py
  key_links:
    - [llm_engine.py](file:///run/media/arun/tool/NeuroRift/ai_wrapper/llm_engine.py)
    - [README.md](file:///run/media/arun/tool/NeuroRift/README.md)
---

# Plan: Replace Ollama with llama.cpp

## Task 1: Environment Setup & Model Automation
- **Action**: Create `scripts/download_model.sh` and `scripts/start_llama.sh`. Update `requirements.txt`.
- **Files**:
  - [NEW] `scripts/download_model.sh`
  - [NEW] `scripts/start_llama.sh`
  - [MODIFY] `requirements.txt`
  - [MODIFY] `setup.py`
- **Verify**:
  - Run `scripts/start_llama.sh --help` (after mock install if needed).
  - Check `requirements.txt` for `llama-cpp-python[server]`.
- **Done**: Scripts exist and dependencies are updated.

## Task 2: Implement Llama Client
- **Action**: Implement `ai_wrapper/llama_client.py` using `httpx` to talk to the local `llama.cpp` server. Support Hermes-2-Pro tool calling format.
- **Files**:
  - [NEW] `ai_wrapper/llama_client.py`
  - [MODIFY] `ai_wrapper/__init__.py`
- **Verify**:
  - Unit test for `LlamaClient` mocking the server response.
- **Done**: `llama_client.py` implemented and exported.

## Task 3: Refactor LLM Engine & Modules
- **Action**: Update `ai_wrapper/llm_engine.py` to use `LlamaClient` instead of direct Ollama HTTP calls. Cleanup hardcoded Ollama references.
- **Files**:
  - [MODIFY] `ai_wrapper/llm_engine.py`
  - [MODIFY] `neurorift_main.py`
  - [MODIFY] `install_script.sh`
- **Verify**:
  - Run `pytest tests/test_ai_features.py` with mocked client.
- **Done**: Codebase no longer references Ollama port 11434.

## Task 4: Documentation & Cleanup
- **Action**: Update `README.md` and `DOCKER.md`. Remove legacy setup references.
- **Files**:
  - [MODIFY] `README.md`
  - [MODIFY] `DOCKER.md`
- **Verify**:
  - Manual review of README instructions.
- **Done**: Documentation reflects the new architecture.
