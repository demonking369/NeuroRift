# Codebase Conventions

## Architectural Patterns
- **Agent Roles**: The application divides responsibilities into distinct agent roles (Planner, Operator, Analyst, Scribe).
- **Asynchronous Processing**: Heavy use of `async`/`await` in Python for concurrency, especially beneficial for executing non-blocking network I/O and subprocess execution.
- **WebSocket Streaming**: OpenClaw (Rust) communicates execution updates back to the orchestrator and web UI continuously.

## Code Style
- **Python Formatting**: Relies heavily on `black` and `pylint`. Maximum line lengths enforce readability.
- **Imports**: standard library imports before third-party ones.
- **Strong Typing**: Python methods leverage type hinting where possible to improve static analysis and document input/output clearly.

## Error Handling
- Use of custom exception classes or graceful fallbacks when LLM execution fails.
- In security contexts (such as XML parsing), safe APIs (`defusedxml`) are strictly mandated.

## Secret Management
- Secrets (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) are managed exclusively via environment variables (`.env`) and Docker environment config injection.
