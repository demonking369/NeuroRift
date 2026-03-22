# Codebase Tech Stack

## Overview
NeuroRift is a terminal-based multi-agent intelligence system built on a polyglot architecture combining Python, Rust, and TypeScript/Next.js.

## Languages & Runtimes
- **Python (3.10+)**: Primary language for the bridge server, orchestrator, and AI module integrations (`modules/`, `neurorift_main.py`).
- **Rust**: High-performance engine for system-level operations and the OpenClaw gateway (`core/`, `Cargo.toml`).
- **TypeScript & Node.js**: Used for the Next.js web dashboard (`web-ui/`).

## Frameworks & Libraries
- **Backend (Python)**:
  - `FastAPI` & `uvicorn` for the bridge server API.
  - `aiohttp` and `asyncio` for asynchronous execution.
  - `langchain-*` (Core, OpenAI, Ollama, Anthropic, Google) for AI agent orchestration.
  - `rich` and `click` for the advanced CLI and terminal UI.
- **Frontend (Web UI)**:
  - `Next.js` (React framework).
  - `Tailwind CSS` for styling.
- **Testing (Python)**:
  - `pytest`, `pytest-asyncio`, `pytest-cov`.
- **Code Quality**:
  - `black`, `pylint`.

## Infrastructure & Deployment
- **Docker & Docker Compose**: The entire stack is containerized, defining services like `ollama`, `neurorift-core` (Python), `rust-engine`, `gateway`, `sandbox-runner`, and `web-ui`.
- **Network**: Uses bridged Docker networking (`neurorift_net`).

## Security Tools Used
- `python-nmap` for network scanning.
- `dnspython` for DNS querying.
- `defusedxml` to prevent XXE attacks.
