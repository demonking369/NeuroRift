# NeuroRift + OpenClaw Boot Sequence (Stabilized)

This runbook initializes NeuroRift as a primary OpenClaw agent with strict sandboxing, approval controls, heartbeat discipline, and deterministic Docker runtime.

## 1) Preflight (mandatory)

Export required runtime env:
- `OPENCLAW_CONFIG_PATH`
- `OPENCLAW_STATE_DIR`
- `OLLAMA_HOST`
- `NEURORIFT_BRIDGE_URL`

Export provider/channel secrets as needed:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY` or `CLAUDE_API_KEY`
- `ZAI_API_KEY` or `Z_AI_API_KEY`
- `OPENCLAW_DISCORD_WEBHOOK_URL` (optional)
- `OPENCLAW_TELEGRAM_BOT_TOKEN` + `OPENCLAW_TELEGRAM_CHAT_ID` (optional)

Run cross-device doctor checks:

```bash
python3 scripts/openclaw_doctor.py
```

## 2) Start deterministic Docker runtime

```bash
docker compose up -d --build gateway neurorift-core rust-engine web-ui ollama sandbox-runner
```

Verify service health:

```bash
docker compose ps
```

## 3) Start NeuroRift FastAPI bridge

```bash
python3 modules/web/bridge_server.py
```

Health check:

```bash
curl -s http://127.0.0.1:8766/health
```

## 4) Start OpenClaw gateway and adapter

```bash
openclaw gateway --config ./openclaw.json5
python3 integrations/openclaw/openclaw_gateway_adapter.py
```

Adapter policy guarantees:
- Terminal-only execution path for operator actions.
- Sandbox workdir enforced at `/workspace`.
- Tool allow/deny lists enforced.
- High-risk operations forwarded for Discord/Telegram approval, timeout auto-deny.

## 5) HEARTBEAT discipline

Read `HEARTBEAT.md` at startup and every configured interval.
- No action needed → emit `HEARTBEAT_OK` only.
- Action needed → generate structured task and log decision.

## 6) Validate end-to-end flow

1. Send a recon request from Discord/Telegram/WhatsApp/Signal.
2. Verify request is processed with isolated session identity.
3. Confirm response returns to originating channel with mention/group policy preserved.
4. Confirm high-risk commands trigger approval forwarder events.
5. Confirm CronService scheduling guard prevents same-second loops.
6. Follow diagnostic events from control stream with:

```bash
openclaw logs.follow
```
