# Quick Task 260322-a01: OpenClaw Notification Layer — Research

**Gathered:** 2026-03-22
**Status:** Ready for planning

## 1. Existing OpenClaw Infrastructure

NeuroRift already has a full OpenClaw Gateway adapter at
`integrations/openclaw/openclaw_gateway_adapter.py`. Key takeaways:

- **Gateway URL**: `ws://127.0.0.1:18789/gateway` (env: `OPENCLAW_WS_URL`)
- **Frame types**: `lifecycle.update`, `event.signal`, `rpc.request`, `rpc.response`
- **Heartbeat**: Every 60s via `event.signal` with `HEARTBEAT_OK`
- **Approval forwarding**: Already has Discord webhook + Telegram bot notification
- **Logger**: `StructuredLogger` emits JSON events to stdout
- **Dependencies**: `websockets`, `httpx` (both already in requirements.txt)

### WebSocket Frame Structure (from existing adapter)

```json
{
  "type": "event.signal",
  "name": "NOTIFICATION",
  "session": { "id": "nr-xxxx", "mode": "isolated" },
  "payload": { ... },
  "ts": 1679500000000
}
```

## 2. Best Approach: Reuse vs. New

**Recommended: Build a lightweight `NotificationDispatcher` that sends
`event.signal` frames through the same gateway WebSocket.**

Rationale:
- The gateway already handles routing to Discord/Telegram
- We only need to add a notification-specific event type
- No need to duplicate the webhook/bot logic already in the adapter
- The `event.signal` frame type is designed for one-way notifications

**Alternative approach (if gateway is offline):** Direct HTTP fallback
to Discord webhook and Telegram API — this is what the existing
`ExecutionApprovalForwarder` already does. We should support both paths.

## 3. Integration Points in Pipeline

| Pipeline Stage | File | Hook Point |
|---|---|---|
| Scan start | `main.py:110` | After recon bridge init |
| Recon complete | `main.py:125` | After `compressor.compress()` |
| Vulnerability found | `ai/executor.py:run()` | Inside the execution loop |
| Critical finding | `ai/executor.py:run()` | Severity check after finding |
| Scan complete | `main.py:146` | After `reporter.generate()` |
| Scan failed | `main.py:121,183` | Exception handlers |

## 4. Common Pitfalls

1. **Blocking the pipeline**: WebSocket sends MUST be async and wrapped
   in `asyncio.create_task()` — never `await` directly in the hot path
2. **Gateway offline**: Must queue notifications and retry, not crash
3. **Credential leakage**: Never log tokens/keys from `notifications.yaml`
4. **Reconnection storms**: Use exponential backoff on WS reconnect
5. **Template injection**: Use `.format_map()` with a safe dict, not f-strings
6. **Config hot-reload**: Don't cache config forever — re-read on each scan start

## 5. Library Choices

- **WebSocket client**: `websockets` (already installed)
- **YAML parsing**: `pyyaml` (already installed)
- **Async queue**: `asyncio.Queue` (stdlib, no dependency)
- **Retry logic**: Manual with exponential backoff (no external dep needed)

## 6. Architecture Recommendation

```
notifications/
├── __init__.py          # exports NotificationDispatcher
├── dispatcher.py        # async dispatcher with queue + retry
├── templates.py         # event templates (dataclass-based)
└── config_loader.py     # reads notifications.yaml safely
```

The dispatcher should be a singleton passed through the pipeline
via dependency injection (constructor arg to Executor, Reporter, etc.)
or registered as a module-level instance in `main.py`.
