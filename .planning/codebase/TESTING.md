# Codebase Testing

## Frameworks
- The Python backend uses `pytest` as its primary test runner.
- The `pytest-asyncio` plugin is essential since much of the core agent execution engine relies on asynchronous operations.
- `pytest-cov` is utilized to track test coverage.

## Structure
- Tests reside in the top-level `tests/` directory.
- `test_*.py` files map generally to subsystems:
  - `test_ai_features.py`: Validates integration of various Langchain orchestrations.
  - `test_security.py`: Ensures security protocols (e.g., stopping XXE via `defusedxml` checks) are enforced across the codebase.
  - `test_notifier.py`: Validates state streaming notifications.

## Execution
- Typical test execution incorporates automated stubbing and mocking. Network calls or LLM API endpoints during unit tests are expected to be patched out to prevent external requests or costs.
