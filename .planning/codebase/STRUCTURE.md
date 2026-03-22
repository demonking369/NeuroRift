# Codebase Structure

## Root Directory Map
The repository is split into distinct logical environments:

### Backend (Python Core)
- `neurorift_main.py`: Primary application entry and orchestrator init.
- `neurorift_cli.py`: Command Line argument parsing subsystem.
- `modules/`: Feature-specific modules categorizing the application's domain logic.
  - `ai/`: Agent specific logic.
  - `recon/`: Logic for invoking reconnaissance tools.
  - `scan/`: Core vulnerability scanning logic.
  - `darkweb/`: Darkweb OSINT / Robin integration.
  - `exploit/`: Exploit testing modules.
  - `session/`: Persistent session tracking.
  - `web/`: HTTP handlers and FastAPI bridging.
- `ai_wrapper/`: Abstract interfaces for Langchain integration across multiple model providers.
- `configs/`: Default configuration schemas (`neurorift_config.json`, etc.).
- `prompts/`: Template libraries for the individual agents (Planner, Operator, Analyst, Scribe).
- `utils/`: Common helpers (logging, formatting, networking constants).

### Execution Engine (Rust)
- `core/`: The workspace root housing Rust packages.
- `neurorift-core/`: The `openclaw` Rust package acting as the high-throughput WebSocket Gateway (`Cargo.toml`, `src/`).

### Frontend (Next.js)
- `web-ui/`: The primary React web application.
  - `src/`: Component, page, and hooks directory.
  - `package.json`: NPM dependencies.
  - `tailwind.config.ts`: Dashboard styling schema.

### Deployment & CI/CD
- `docker/`: Contains specialized Dockerfiles for different environments.
  - `docker/neurorift/Dockerfile`: Base image for Python backend.
  - `docker/openclaw/Dockerfile`: Base image for Rust engine.
  - `docker/web-ui/Dockerfile`: Base image for Next.js dashboard.
- `docker-compose.yml`: Comprehensive local compose file connecting all microservices (DBs, Ollama, Core, Gateway, Sandbox, Web-UI).
- `.github/`: CI/CD workflows for validation.

## Naming Conventions
- Python files follow standard `snake_case.py`.
- Rust files follow `snake_case.rs`.
- React components typically use `PascalCase.tsx`.
- Configuration files end in `.json` or `.json5`. Document templates use Markdown (`.md`).
