# Codebase Architecture

## System Design Pattern
NeuroRift operates on a **Multi-Agent Orchestration Architecture** with human-in-the-loop (HITL) manual oversight. The system is distributed across three main operational planes:

1. **The Core Orchestrator (Python bridge)**: Manages intelligence routing, LLM inferences via Langchain, state storage, task coordination, and module interaction. 
2. **The Execution Engine (Rust openclaw)**: A high-performance WebSockets gateway that connects the orchestrator to containerized sandboxed environments for safe execution of security tools. Handles streaming of terminal outputs.
3. **The Control Plane (Next.js Dashboard)**: A modern, real-time web UI that serves as the mission control for analysts to monitor agent actions, approve HITL requests, and execute tools manually.

## Data Flow
- User interactions (Dashboard or CLI) define an initial `Task` or `Mission`.
- The `NR Planner` generates an execution plan and updates the centralized Task State Memory.
- The `NR Operator` attempts to fulfill tasks, utilizing tools like Nmap or ProjectDiscovery via the Rust sandboxed environments.
- High-risk operations request explicit human authorization via the Bridge REST API to the control plane.
- The `NR Analyst` analyzes task outputs stored as JSON artifacts.
- The `NR Scribe` aggregates findings into actionable markdown/PDF reports.

## Subsystems
- **AI/LLM Integration (`ai_wrapper/`)**: Encapsulates LLM usage into modular clients for local (Ollama) and remote models.
- **Workflow Modules (`modules/`)**: Contain domains of expertise (e.g., `recon/`, `scan/`, `darkweb/`, `exploit/`).
- **State Checkpoints**: The architecture persists task states every 5 minutes in `/data/neurorift/sessions` to allow pause/resume natively.
- **Security Sandboxing**: The `sandbox-runner` container isolates potentially dangerous terminal workflows so arbitrary shell outputs remain distinct from the host file system.

## Entry Points
- `neurorift_main.py` & `neurorift_cli.py`: The Python entrypoints for command-line parsing and mode switching.
- `web-ui/src/app/page.tsx`: The primary Next.js page that interfaces via Server-Sent Events/WebSockets to the backend.
