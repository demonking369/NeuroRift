# NeuroRift + OpenClaw Boot Sequence

This runbook initializes NeuroRift as a primary OpenClaw agent and loads proactive monitoring.

## 1) Preflight

1. Export provider and channel secrets:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY` or `CLAUDE_API_KEY`
   - `ZAI_API_KEY` or `Z_AI_API_KEY`
   - `OPENCLAW_DISCORD_WEBHOOK_URL` (optional)
   - `OPENCLAW_TELEGRAM_BOT_TOKEN` + `OPENCLAW_TELEGRAM_CHAT_ID` (optional)
2. Confirm services:
   - NeuroRift FastAPI bridge on `:8766`
   - OpenClaw WebSocket gateway on `:18789`

## 2) Start NeuroRift FastAPI bridge

```bash
python3 modules/web/bridge_server.py
```

Health check:

```bash
curl -s http://127.0.0.1:8766/health
```

## 3) Start OpenClaw gateway

Use your OpenClaw runtime with the unified config:

```bash
openclaw gateway --config ./openclaw.json5
```

## 4) Start the adapter bridge

```bash
python3 integrations/openclaw/openclaw_gateway_adapter.py
```

The adapter maps NeuroRift internal calls into OpenClaw RPC methods:
- `run_terminal_cmd -> exec`
- `read_file -> read`
- `write_file -> write`
- `process_state -> process`

## 5) Load HEARTBEAT checklist

Review and execute `HEARTBEAT.md` at startup and once every shift.

## 6) Validate end-to-end flow

1. Send a recon request from Discord/Telegram/WhatsApp/Signal.
2. Verify the request opens an `isolated` session.
3. Confirm high-risk commands trigger approval forwarder messages.
4. Confirm scheduled job appears in CronService (`weekly-attack-surface-recon`).
