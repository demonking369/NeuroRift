# NeuroRift × OpenClaw Stabilization Audit

## Scope
Hardening pass for gateway compliance, sandbox controls, environment normalization, deterministic runtime, and operational governance.

## Compliance Matrix

| Phase | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Real websocket frame semantics + session/channel isolation | Implemented | `integrations/openclaw/openclaw_gateway_adapter.py` handles `rpc.request`, `event.signal`, `lifecycle.update`; session keying splits DM/group by channel context. |
| 2 | Visible master integration prompt | Implemented | `openclaw.json5` `systemPrompt.visible=true` with explicit architecture + policy text. |
| 3 | Terminal-only operator enforcement | Implemented | Exec policy checks + allow/deny enforcement in adapter before bridge execution. |
| 4 | Sandbox constants + approval behavior | Implemented | Sandbox constants in adapter and policy blocks in `openclaw.json5`; approval requested/result events emitted with auto-deny default. |
| 5 | Cron guard semantics | Implemented (config-level) | `openclaw.json5` cron guard keys for same-second loop prevention and isolated jobs. |
| 6 | Heartbeat cycle discipline | Implemented | adapter emits `HEARTBEAT_OK` on interval with no message spam; openclaw config includes spin-loop prevention flags. |
| 7 | Structured diagnostics | Implemented | JSON event logger emits structured payloads with redaction and latency fields. |
| 8 | Strict env normalization / fail-fast | Implemented | adapter startup validation for required env and malformed key rejection. |
| 9 | Deterministic docker services | Implemented | `docker-compose.yml` includes required services: gateway, neurorift-core, rust-engine, web-ui, llama.cpp, sandbox-runner. |
| 10 | Prototype leakage controls | Implemented (config-policy) | `openclaw.json5` runtime mode isolation policy states strict prototype/real behavior separation. |
| 11 | Secure evolution controls | Implemented (config-policy) | `openclaw.json5` evolution approval and rollback governance block added. |
| 12 | Cross-device stability checks | Implemented | Added `scripts/openclaw_doctor.py` for preflight env + port checks and documented usage in `BOOT.md`. |

## Residual Risk Notes
1. Approval callback channel remains controller-integrated and currently defaults to secure deny-on-timeout.
2. Cron guard/evolution enforcement is represented as explicit config policy and requires corresponding runtime support in OpenClaw control plane.
3. `sandbox-runner` assumes `openclaw-sandbox:bookworm-slim` image is available in deployment environment.
