# Quick Task 260322-icf: Research Findings

## 1. Current State of the Codebase
- **Syntax Errors**: A global find-and-replace appears to have been run previously, replacing the word `ollama` with `llama.cpp`. This corrupted Python code in `modules/darkweb/robin/llm_utils.py`, turning `ChatOllama` into `Chatllama.cpp`, which is invalid syntax. 
- **Ollama References**: There are still multiple lingering references to `ollama` in variables (e.g., `def __init__(self, ollama: LocalAIClient)` in `modules/ai/agents.py`), `DOCKER.md`, `install_script.sh`, and `modules/darkweb/robin/llm_utils.py`.
- **Test Infrastructure**: `pytest` is available but a previous test suite exists that we failed against during the pipeline upgrade.
- **Flake8**: Not installed on the system globally. We may need to use local linting or install it, or skip it and rely on `py_compile` and manual inspection.

## 2. Integration & Pitfalls
- **llm_utils.py**: The darkweb robin module heavily relies on Langchain Ollama packages (`langchain_ollama` and `ChatOllama`). Migrating this to `llama.cpp` requires swapping to `langchain_community.chat_models.ChatOpenAI` pointed at `localhost:8080`, since `llama.cpp` is running an OpenAI-compatible server.
- **Scope Parsing & Enforcement**: The user explicitly requested unit tests for `scope_parser` and `scope_enforcer`. We need to verify these files exist and build robust fixtures.
- **Session State & Orchestration**: Need to ensure the new AI Orchestrator while loop logic plays nicely with `session_state`.

## 3. Plan Formulation Strategy
The bug hunt must be systematic:
1. Fix the glaring syntax errors first.
2. Purge all Ollama legacy code correctly.
3. Write and pass the Unit Tests (PHASE 2).
4. Write and pass the Integration Tests (PHASE 3) and Edge Case tests (PHASE 4).
5. Generate the final Bug Hunt Report.
