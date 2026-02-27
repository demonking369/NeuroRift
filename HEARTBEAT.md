# HEARTBEAT Checklist (Proactive Monitoring)

Run this checklist continuously while the gateway is active.

## Runtime Liveness

- [ ] OpenClaw WebSocket is reachable on `ws://127.0.0.1:18789/gateway`
- [ ] NeuroRift FastAPI bridge healthy on `http://127.0.0.1:8766/health`
- [ ] Adapter session started as `isolated`
- [ ] `yieldMs` push updates are flowing (no tight polling loops)

## Security Controls

- [ ] Docker sandbox image in use: `openclaw-sandbox:bookworm-slim`
- [ ] Sandboxed enforcement for `nmap`, `subfinder`, `httpx`
- [ ] High-risk command patterns are intercepted
- [ ] Approval timeout defaults to **deny**

## Channel & Workflow Routing

- [ ] Inbound triggers active for Discord/Telegram/WhatsApp/Signal
- [ ] Security prompts route to NeuroRift recon workflow
- [ ] Planner -> Manus Tool Selector -> Operator -> Analyst/Cursor pipeline executes in order

## Memory & Persona

- [ ] Session-memory hooks loaded under `neurorift-session-memory`
- [ ] Attack surface context persisted between sessions
- [ ] `SOUL.md` persona loaded for responses

## Scheduling

- [ ] CronService job `weekly-attack-surface-recon` registered
- [ ] `computeNextRunAtMs` is enabled
- [ ] Notifications are pushed on completion/failure

## Environment Normalization

- [ ] Anthropic key normalized (`ANTHROPIC_API_KEY`)
- [ ] OpenAI key normalized (`OPENAI_API_KEY`)
- [ ] Z.AI key normalized (`ZAI_API_KEY`)
