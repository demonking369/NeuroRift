#!/usr/bin/env python3
"""OpenClaw Gateway adapter for NeuroRift.

Production hardening goals:
- strict gateway frame handling (rpc/event/lifecycle)
- isolated session routing by channel/user/group context
- terminal-only operator execution policy
- sandbox/tool allow-deny enforcement for exec calls
- high-risk approval forwarding with structured logs
- heartbeat discipline and async yield notifications
- strict environment normalization and startup validation
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

import httpx
import websockets

DEFAULT_SANDBOX_WORKDIR = "/workspace"
DEFAULT_TOOL_ALLOW = {"nmap", "subfinder", "httpx"}
DEFAULT_TOOL_DENY = {
    "rm",
    "reboot",
    "shutdown",
    "poweroff",
    "mkfs",
    "dd",
    "init",
}

HIGH_RISK_PATTERNS = [
    re.compile(r"nmap\s+.*-p-"),
    re.compile(r"nmap\s+.*--script"),
    re.compile(r"\bsqlmap\b"),
    re.compile(r"\bmsfconsole\b"),
    re.compile(r"rm\s+-rf\s+"),
    re.compile(r"curl\s+.+\|\s*sh"),
]

TOOL_METHOD_MAP = {
    "run_terminal_cmd": "exec",
    "terminal": "exec",
    "read_file": "read",
    "file_read": "read",
    "write_file": "write",
    "file_write": "write",
    "process_state": "process",
    "workflow_state": "process",
}

REQUIRED_ENV = [
    "OPENCLAW_CONFIG_PATH",
    "OPENCLAW_STATE_DIR",
    "OLLAMA_HOST",
    "NEURORIFT_BRIDGE_URL",
]


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def normalize_env() -> Dict[str, str]:
    """Normalize provider and runtime env keys and fail fast for malformed values."""
    out = dict(os.environ)

    anthropic = out.get("ANTHROPIC_API_KEY") or out.get("CLAUDE_API_KEY")
    openai = out.get("OPENAI_API_KEY")
    zai = out.get("ZAI_API_KEY") or out.get("Z_AI_API_KEY")

    if anthropic:
        out["ANTHROPIC_API_KEY"] = anthropic.strip()
    if openai:
        out["OPENAI_API_KEY"] = openai.strip()
    if zai:
        out["ZAI_API_KEY"] = zai.strip()

    for key in REQUIRED_ENV:
        value = out.get(key)
        if not value or not value.strip():
            raise RuntimeError(f"Missing required environment variable: {key}")

    malformed = [
        k
        for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ZAI_API_KEY")
        if out.get(k, "").strip().startswith("$")
    ]
    if malformed:
        raise RuntimeError(f"Malformed provider keys: {', '.join(malformed)}")

    out["OPENCLAW_REDACT_LOGS"] = (
        "1" if _truthy(out.get("OPENCLAW_REDACT_LOGS", "1")) else "0"
    )
    return out


@dataclass
class ApprovalResult:
    approved: bool
    reason: str


class StructuredLogger:
    def __init__(self) -> None:
        self.redact = _truthy(os.getenv("OPENCLAW_REDACT_LOGS", "1"))

    def _sanitize(self, value: Any) -> Any:
        if not self.redact:
            return value
        if isinstance(value, str):
            value = re.sub(
                r"(api[_-]?key|token|secret)=([^\s]+)",
                r"\1=[REDACTED]",
                value,
                flags=re.I,
            )
            value = re.sub(r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED]", value)
            return value
        if isinstance(value, dict):
            redacted = {}
            for k, v in value.items():
                if any(s in k.lower() for s in ("token", "secret", "key", "password")):
                    redacted[k] = "[REDACTED]"
                else:
                    redacted[k] = self._sanitize(v)
            return redacted
        if isinstance(value, list):
            return [self._sanitize(v) for v in value]
        return value

    def emit(self, event: str, **payload: Any) -> None:
        envelope = {
            "event": event,
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "payload": self._sanitize(payload),
        }
        print(json.dumps(envelope, ensure_ascii=False), flush=True)


class ExecutionApprovalForwarder:
    """Forwards high-risk command approvals to Discord and Telegram."""

    def __init__(self, logger: StructuredLogger, timeout_seconds: int = 300) -> None:
        self.logger = logger
        self.timeout_seconds = timeout_seconds

    def _is_high_risk(self, command: str) -> bool:
        return any(p.search(command) for p in HIGH_RISK_PATTERNS)

    async def evaluate(
        self, command: str, session_id: str, correlation_id: str
    ) -> ApprovalResult:
        if not self._is_high_risk(command):
            return ApprovalResult(approved=True, reason="low-risk command")

        message = (
            "⚠️ OpenClaw approval required\n"
            f"session={session_id}\n"
            f"request={correlation_id}\n"
            f"command={command}\n"
            "Reply with APPROVE or DENY in your control channel."
        )
        self.logger.emit(
            "approval.requested", session_id=session_id, request_id=correlation_id
        )
        await asyncio.gather(
            self._notify_discord(message),
            self._notify_telegram(message),
            return_exceptions=True,
        )

        # Human callback hook should flip result in external controller.
        await asyncio.sleep(0)
        result = ApprovalResult(
            approved=False, reason="approval pending/timeout -> deny"
        )
        self.logger.emit(
            "approval.result",
            session_id=session_id,
            request_id=correlation_id,
            approved=result.approved,
            reason=result.reason,
        )
        return result

    async def _notify_discord(self, content: str) -> None:
        webhook = os.getenv("OPENCLAW_DISCORD_WEBHOOK_URL")
        if not webhook:
            return
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(webhook, json={"content": content})

    async def _notify_telegram(self, content: str) -> None:
        token = os.getenv("OPENCLAW_TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("OPENCLAW_TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": chat_id, "text": content})


class NeuroRiftOpenClawAdapter:
    def __init__(self) -> None:
        self.logger = StructuredLogger()
        self.session_id = f"nr-{uuid.uuid4().hex[:12]}"
        self.request_timeout = 120
        self.bridge_url = os.getenv("NEURORIFT_BRIDGE_URL", "http://127.0.0.1:8766")
        self.gateway_ws_url = os.getenv(
            "OPENCLAW_WS_URL", "ws://127.0.0.1:18789/gateway"
        )
        self.yield_ms = int(os.getenv("OPENCLAW_YIELD_MS", "1500"))
        self.heartbeat_interval = int(os.getenv("OPENCLAW_HEARTBEAT_INTERVAL_S", "60"))
        self.approval_forwarder = ExecutionApprovalForwarder(self.logger)
        self._stop_event = asyncio.Event()
        self._last_heartbeat = 0.0

    @staticmethod
    def _map_method(neurorift_tool_call: Dict[str, Any]) -> str:
        call_type = str(neurorift_tool_call.get("type", "")).strip()
        return TOOL_METHOD_MAP.get(call_type, "process")

    @staticmethod
    def _extract_command_preview(tool_call: Dict[str, Any], rpc_method: str) -> str:
        if rpc_method != "exec":
            return ""

        for key in ("command", "cmd", "shell", "input"):
            value = tool_call.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        payload = tool_call.get("payload")
        if isinstance(payload, dict):
            for key in ("command", "cmd"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        return json.dumps(tool_call, ensure_ascii=False)

    @staticmethod
    def _resolve_session_context(event: Dict[str, Any]) -> Dict[str, Any]:
        session = event.get("session") or {}
        channel = (event.get("channel") or session.get("channel") or "unknown").lower()
        user_id = event.get("userId") or session.get("userId") or "anonymous"
        group_id = event.get("groupId") or session.get("groupId")
        mention_policy = event.get("mentionPolicy") or "required"

        if group_id:
            session_key = f"{channel}:group:{group_id}"
        else:
            session_key = f"{channel}:dm:{user_id}"

        return {
            "channel": channel,
            "userId": user_id,
            "groupId": group_id,
            "sessionKey": session_key,
            "mentionPolicy": mention_policy,
        }

    def _validate_exec_policy(self, command: str) -> None:
        base_cmd = command.strip().split()[0] if command.strip() else ""
        if not base_cmd:
            raise ValueError("Empty exec command")
        if base_cmd in DEFAULT_TOOL_DENY:
            raise PermissionError(f"Tool denied by policy: {base_cmd}")
        if base_cmd not in DEFAULT_TOOL_ALLOW:
            raise PermissionError(f"Tool not in allow-list: {base_cmd}")

    async def _call_neurorift(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            response = await client.post(f"{self.bridge_url}/execute", json=payload)
            response.raise_for_status()
            return response.json()

    async def _emit_heartbeat_if_due(
        self, ws: websockets.WebSocketClientProtocol
    ) -> None:
        now = time.time()
        if now - self._last_heartbeat < self.heartbeat_interval:
            return
        self._last_heartbeat = now
        heartbeat = {
            "type": "event.signal",
            "name": "HEARTBEAT_OK",
            "session": {"id": self.session_id, "mode": "isolated"},
            "ts": int(now * 1000),
        }
        await ws.send(json.dumps(heartbeat))
        self.logger.emit("heartbeat.ok", session_id=self.session_id)

    async def _build_rpc_frame(self, event: Dict[str, Any]) -> Dict[str, Any]:
        tool_call = event.get("payload", {})
        rpc_method = self._map_method(tool_call)
        command_preview = self._extract_command_preview(tool_call, rpc_method)
        correlation_id = event.get("id") or str(uuid.uuid4())
        started = time.time()
        session_ctx = self._resolve_session_context(event)

        try:
            if rpc_method == "exec":
                self._validate_exec_policy(command_preview)
                approval = await self.approval_forwarder.evaluate(
                    command_preview,
                    session_ctx["sessionKey"],
                    str(correlation_id),
                )
                if not approval.approved:
                    return {
                        "type": "rpc.response",
                        "id": correlation_id,
                        "session": {
                            "id": session_ctx["sessionKey"],
                            "mode": "isolated",
                        },
                        "error": {
                            "code": "approval_required",
                            "message": approval.reason,
                        },
                    }

            bridged = await self._call_neurorift(tool_call)
        except PermissionError as exc:
            return {
                "type": "rpc.response",
                "id": correlation_id,
                "session": {"id": session_ctx["sessionKey"], "mode": "isolated"},
                "error": {"code": "policy_denied", "message": str(exc)},
            }
        except ValueError as exc:
            return {
                "type": "rpc.response",
                "id": correlation_id,
                "session": {"id": session_ctx["sessionKey"], "mode": "isolated"},
                "error": {"code": "invalid_request", "message": str(exc)},
            }

        elapsed_ms = int((time.time() - started) * 1000)
        self.logger.emit(
            "exec.finished" if rpc_method == "exec" else "webhook.processed",
            session_id=session_ctx["sessionKey"],
            method=rpc_method,
            latency_ms=elapsed_ms,
            tokens=bridged.get("usage", {}).get("tokens"),
            cost=bridged.get("usage", {}).get("cost"),
        )

        return {
            "type": "rpc.response",
            "id": correlation_id,
            "session": {
                "id": session_ctx["sessionKey"],
                "mode": "isolated",
                "pipeline": [
                    "planner",
                    "tool-selector/manus",
                    "operator",
                    "analyst/cursor",
                ],
                "channel": session_ctx["channel"],
                "mentionPolicy": session_ctx["mentionPolicy"],
            },
            "result": {
                "method": rpc_method,
                "source": "neurorift-fastapi",
                "bridgePort": 8766,
                "gatewayPort": 18789,
                "yieldMs": self.yield_ms,
                "push": True,
                "sandbox": {
                    "image": "openclaw-sandbox:bookworm-slim",
                    "workdir": DEFAULT_SANDBOX_WORKDIR,
                },
                "payload": bridged,
            },
            "ts": int(time.time() * 1000),
        }

    async def _lifecycle_loop(self, ws: websockets.WebSocketClientProtocol) -> None:
        while not self._stop_event.is_set():
            await asyncio.sleep(5)
            await self._emit_heartbeat_if_due(ws)

    async def run(self) -> None:
        os.environ.update(normalize_env())

        def stop_handler(*_: Any) -> None:
            self._stop_event.set()

        signal.signal(signal.SIGTERM, stop_handler)
        signal.signal(signal.SIGINT, stop_handler)

        async with websockets.connect(
            self.gateway_ws_url, ping_interval=20, ping_timeout=20
        ) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "lifecycle.update",
                        "state": "starting",
                        "session": {
                            "id": self.session_id,
                            "mode": "isolated",
                            "agent": "neurorift-primary",
                            "memoryHook": "openclaw-session-memory",
                            "personaFile": "SOUL.md",
                        },
                    }
                )
            )

            lifecycle_task = asyncio.create_task(self._lifecycle_loop(ws))
            try:
                while not self._stop_event.is_set():
                    incoming = await ws.recv()
                    event = json.loads(incoming)
                    event_type = event.get("type")

                    if event_type == "rpc.request":
                        frame = await self._build_rpc_frame(event)
                        await ws.send(json.dumps(frame))
                    elif event_type == "event.signal":
                        self.logger.emit(
                            "webhook.processed",
                            signal=event.get("name"),
                            channel=event.get("channel"),
                        )
                    elif event_type == "lifecycle.update":
                        self.logger.emit(
                            "lifecycle.update",
                            state=event.get("state"),
                            session=event.get("session"),
                        )
                    else:
                        self.logger.emit("gateway.unknown_frame", frame_type=event_type)
            finally:
                lifecycle_task.cancel()
                await ws.send(
                    json.dumps(
                        {
                            "type": "lifecycle.update",
                            "state": "stopped",
                            "session": {"id": self.session_id, "mode": "isolated"},
                        }
                    )
                )


if __name__ == "__main__":
    asyncio.run(NeuroRiftOpenClawAdapter().run())
