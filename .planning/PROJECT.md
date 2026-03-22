# NeuroRift Project

## Overview
NeuroRift is an orchestrated multi-agent intelligence system for security research. It uses NeuroCore (embedded llama.cpp bindings) for local AI inference and OpenClaw for real-time notifications across 22+ platforms.

## Core Value
High-performance, local-first AI orchestration for security tools with zero external LLM dependencies.

## Requirements

### Validated
- ✓ Multi-agent orchestration (Planner, Operator, Analyst, Scribe)
- ✓ Security tool integration (Nmap, ProjectDiscovery)
- ✓ NeuroCore inference engine (direct C bindings, multi-model routing)
- ✓ OpenClaw notification layer (async dispatcher, severity filtering)
- ✓ Persistent session and artifact management
- ✓ Scope-file driven autonomous pipeline
- ✓ CLI interface

### Active — Milestone 2: Web Mode V3 Remake
- [ ] FastAPI WebSocket backend
- [ ] Next.js + Tailwind dashboard with 8 panels
- [ ] Professional cyberpunk dark theme + clean light toggle
- [ ] Mobile responsive (phone-first for notification follow-up)
- [ ] Real-time WebSocket throughout (no polling, no mock data)

### Out of Scope
- Adding new security tools
- Changing the Rust execution engine
- Modifying NeuroCore or OpenClaw internals

## Current Milestone: v2.0 Web Mode V3

**Goal:** Build a complete, production-grade web dashboard that surfaces all NeuroRift capabilities through a real-time, mobile-responsive interface.

**Target features:**
- 8 dashboard panels with live WebSocket data
- FastAPI backend with WebSocket hub
- Dual theme (cyberpunk dark / clean light)
- Mobile responsive design

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js + Tailwind | Already in codebase, proven stack | Keep |
| FastAPI backend | Clean separation, native WebSocket support, async | New |
| Cyberpunk dark theme | Professional aesthetic matching security domain | Primary |
| No mock data | Dashboard shows real state or explicit offline indicator | Enforced |

---
*Last updated: 2026-03-22 — Milestone v2.0 started*
