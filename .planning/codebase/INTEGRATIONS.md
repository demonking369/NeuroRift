# Codebase Integrations

## AI Model Providers
- **Local AI**: Fully integrated with `Ollama` for running local large language models (e.g., `llama3.2`). Runs as a dedicated container in the Docker compose stack.
- **Cloud AI**: Supports major cloud providers via Langchain:
  - OpenAI
  - Anthropic
  - Google GenAI 

## External Security Tools
NeuroRift orchestrates various external security tools for reconnaissance and vulnerability assessment:
- **ProjectDiscovery Suite**: Integrates with `subfinder`, `nuclei`.
- **Nmap**: Network mapping and port scanning.
- **WhatWeb**: Technology profiling.
- **FFUF**: Web fuzzing (mentioned in Web Control Plane).

## APIs & Data Feeds
- **Dark Web Intelligence**: Integrates with the Tor network via a SOCKS5 proxy (`PySocks`, defaults to `socks5h://127.0.0.1:9050`). Uses Robin integration for `.onion` service scraping and semantic search.
- **Search Engines**: Uses `duckduckgo-search` for OSINT querying.

## System Communication
- **Bridge API**: The Python `neurorift-core` acts as a central HTTP/REST bridge (`http://neurorift-core:8766`).
- **WebSockets Engine**: The Rust engine (`openclaw`) acts as a WebSocket gateway (`0.0.0.0:18789` / `18765`) to communicate state to the frontend and execute high-performance tasks.
