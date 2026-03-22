---
must_haves:
  - Fix all broken `Chatllama.cpp` global string replacements in modules/darkweb/robin/llm_utils.py
  - Phase 1: All static analysis must pass silently (flake8 and python -m py_compile)
  - Phase 2: Create unit tests for scope enforcement, LlamaClient edge cases, recon pipelines, and planners.
  - Phase 3: Create full end-to-end integration tests using mock outputs.
  - Phase 4: Edge case security tests implemented (e.g. disk space error, blank inputs).
  - Phase 5: Produce passing test suites (0 failures).
  - Phase 6: Produce BUG_HUNT_REPORT.md.
---

# Plan: Full Feature Test, Bug Hunt & Auto Fix

## Task 1: Phase 1 & 2 - Static Analysis Fixes and Unit Testing
- **files**: `modules/darkweb/robin/llm_utils.py`, `tests/test_scope_parser.py`, `tests/test_scope_enforcer.py`, `tests/test_llama_client.py`, `tests/test_recon/*`, `tests/test_tools/*`, `tests/test_session_state.py`, `tests/test_reporter.py`, `tests/test_planner.py`
- **action**: Revert the global replacement syntax errors, clean up any lingering `ollama` endpoints in the `install_script.sh` or `DOCKER.md`. Then write individual focused unit tests for every critical component listed in Phase 2, ensuring they capture both happy paths and edge cases as required.
- **verify**: `python3 -m py_compile` passes; `pytest tests/ -v` executes successfully.
- **done**: false

## Task 2: Phase 3 & 4 - Integration and Edge Case Testing
- **files**: `tests/integration/test_scope_to_enforcer.py`, `tests/integration/test_recon_pipeline.py`, `tests/integration/test_planner_to_executor.py`, `tests/integration/test_full_pipeline_mock.py`, `tests/test_edge_cases.py`
- **action**: Set up integration directory and mock pipelines for llama.cpp, tools, and the overarching AI orchestrator loop. Build exhaustive edge case unit tests prioritizing inputs that cause standard failures (blank inputs, timeout, max tokens, unencoded URLs).
- **verify**: `pytest tests/integration tests/test_edge_cases.py` run properly.
- **done**: false

## Task 3: Phase 5 & 6 - Bug Fix Loop and Final Reporting
- **files**: Core library code, `BUG_HUNT_REPORT.md`, `260322-icf-SUMMARY.md`
- **action**: Execute the test suites, document the bugs encountered, systematically fix them across the codebase, and then re-execute. Distill all test results and deferred fixes into `BUG_HUNT_REPORT.md` and complete the quick-task workflow.
- **verify**: All tests pass seamlessly. Final report matches requested outputs.
- **done**: false
