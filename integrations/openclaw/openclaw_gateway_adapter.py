#!/usr/bin/env python3
"""OpenClaw Gateway adapter for NeuroRift.

Bridges NeuroRift FastAPI commands with OpenClaw RPC frames and adds:
- isolated session pipeline metadata
- high-risk execution approval forwarding
- environment key normalization
- push/yield async response handling
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
import websockets

BRIDGE_URL = os.getenv("NEURORIFT_BRIDGE_URL", "http://127.0.0.1:8766")
GATEWAY_WS_URL = os.getenv("OPENCLAW_WS_URL", "ws://127.0.0.1:18789/gateway")
YIELD_MS = int(os.getenv("OPENCLAW_YIELD_MS", "1500"))


def normalize_env() -> Dict[str, str]:
    """Normalize provider keys to avoid auth drift across providers."""
    out = dict(os.environ)

    anthropic = out.get("ANTHROPIC_API_KEY") or out.get("CLAUDE_API_KEY")
    openai = out.get("OPENAI_API_KEY")
    zai = out.get("ZAI_API_KEY") or out.get("Z_AI_API_KEY")

    if anthropic:
        out["ANTHROPIC_API_KEY"] = anthropic
    if openai:
        out["OPENAI_API_KEY"] = openai
    if zai:
        out["ZAI_API_KEY"] = zai

    return out


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


@dataclass
class ApprovalResult:
    approved: bool
    reason: str


class ExecutionApprovalForwarder:
    """Forwards high-risk command approvals to Discord and Telegram."""

    def __init__(self, timeout_seconds: int = 300) -> None:
        self.timeout_seconds = timeout_seconds

    def _is_high_risk(self, command: str) -> bool:
        return any(p.search(command) for p in HIGH_RISK_PATTERNS)

    async def evaluate(self, command: str, session_id: str) -> ApprovalResult:
        if not self._is_high_risk(command):
            return ApprovalResult(approved=True, reason="low-risk command")

        message = (
            "⚠️ OpenClaw approval required\n"
            f"session={session_id}\n"
            f"command={command}\n"
            "Reply with APPROVE or DENY in your control channel."
        )
        await asyncio.gather(
            self._notify_discord(message),
            self._notify_telegram(message),
            return_exceptions=True,
        )

        # Placeholder for channel callback integration.
        # Default-safe behavior is deny-on-timeout.
        await asyncio.sleep(0)
        return ApprovalResult(approved=False, reason="approval pending/timeout -> deny")

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
        self.session_id = f"nr-{uuid.uuid4().hex[:12]}"
        self.request_timeout = 120
        self.approval_forwarder = ExecutionApprovalForwarder()

    @staticmethod
    def _map_method(neurorift_tool_call: Dict[str, Any]) -> str:
        call_type = neurorift_tool_call.get("type", "")
        return TOOL_METHOD_MAP.get(call_type, "process")

    @staticmethod
    def _extract_command_preview(tool_call: Dict[str, Any], rpc_method: str) -> str:
        if rpc_method != "exec":
            return ""

        for key in ("command", "cmd", "shell", "input"):
            value = tool_call.get(key)
            if isinstance(value, str) and value.strip():
                return value

        payload = tool_call.get("payload")
        if isinstance(payload, dict):
            for key in ("command", "cmd"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        return json.dumps(tool_call, ensure_ascii=False)

    async def _call_neurorift(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            response = await client.post(f"{BRIDGE_URL}/execute", json=payload)
            response.raise_for_status()
            return response.json()

    async def _build_rpc_frame(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        rpc_method = self._map_method(tool_call)
        command_preview = self._extract_command_preview(tool_call, rpc_method)

        if rpc_method == "exec":
            approval = await self.approval_forwarder.evaluate(
                command_preview, self.session_id
            )
            if not approval.approved:
                return {
                    "type": "rpc.reject",
                    "id": str(uuid.uuid4()),
                    "session": {"id": self.session_id, "mode": "isolated"},
                    "error": {
                        "code": "approval_required",
                        "message": approval.reason,
                    },
                }

        bridged = await self._call_neurorift(tool_call)

        return {
            "type": "rpc.request",
            "id": str(uuid.uuid4()),
            "session": {
                "id": self.session_id,
                "mode": "isolated",
                "pipeline": [
                    "planner",
                    "tool-selector/manus",
                    "operator",
                    "analyst/cursor",
                ],
            },
            "method": rpc_method,
            "params": {
                "source": "neurorift-fastapi",
                "bridgePort": 8766,
                "gatewayPort": 18789,
                "yieldMs": YIELD_MS,
                "payload": bridged,
            },
            "ts": int(time.time() * 1000),
        }

    async def run(self) -> None:
        os.environ.update(normalize_env())

        async with websockets.connect(
            GATEWAY_WS_URL, ping_interval=20, ping_timeout=20
        ) as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "session.start",
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

            while True:
                incoming = await ws.recv()
                event = json.loads(incoming)
                if event.get("type") != "neurorift.tool_call":
                    continue

                frame = await self._build_rpc_frame(event.get("payload", {}))
                await ws.send(json.dumps(frame))


if __name__ == "__main__":
    asyncio.run(NeuroRiftOpenClawAdapter().run())
