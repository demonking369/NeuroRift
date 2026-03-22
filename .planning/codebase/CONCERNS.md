# Codebase Concerns & Technical Debt

## Known Issues & Vulnerabilities
- **Integration Complexity**: The polyglot microservice architecture spanning Python (AI Orchestration/API), Rust (OpenClaw WebSocket Gateway), and TypeScript (Next.js Dashboard) relies heavily on Docker networks operating perfectly. Any network latency or WebSocket disconnection can result in untracked state.
- **Beta Phase Volatility**: The README mentions "🚧 THIS PROJECT IS CURRENTLY IN ACTIVE DEVELOPMENT (BETA Phase) 🚧". Core features are functional, but edge cases during complex agent interactions may cause hangs or crashes.
- **LLM Non-Determinism**: Dependency on LLMs means the `NR Planner`'s execution plan might vary unpredictably between runs, making debugging and reproducing end-to-end bugs difficult.

## Technical Debt
- **End-to-End Testing**: Current pytest files (`test_ai_features.py`, `test_security.py`) are strictly unit or mocked integration tests. There appears to be a lack of comprehensive end-to-end (E2E) testing that spin up the full Docker compose environment to simulate a real user session.
- **Secret Management**: While `.env` is used, the configuration requires storing API keys in plain-text inside the file or Docker orchestration, lacking an integrated Vault or KMS solution for extremely robust key handling.

## Fragile Areas
- **Sandbox Runner Validation**: The bridge assumes the sandbox cleanly captures command executions without side effects on the host. Any escape from the `openclaw-sandbox` could be catastrophic, necessitating extremely stringent monitoring.
