#!/usr/bin/env python3
"""NeuroRift tool: Race condition testing via concurrent HTTP requests."""

import asyncio
import httpx
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "URL endpoint to test for race conditions"},
        "concurrency": {"type": "integer", "description": "Number of concurrent requests", "default": 20},
        "method": {"type": "string", "description": "HTTP method", "default": "POST"},
    }
}


async def _race(target: str, concurrency: int, method: str):
    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        fn = client.post if method.upper() == "POST" else client.get
        tasks = [fn(target) for _ in range(concurrency)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
    codes = [r.status_code for r in responses if isinstance(r, httpx.Response)]
    return codes


class RaceConditionTool:
    name = "race_condition"
    description = "Test for race conditions using concurrent request bursts"

    @staticmethod
    def schema(): return SCHEMA

    def run(self, target: str, concurrency: int = 20, method: str = "POST") -> ToolResult:
        try:
            codes = asyncio.run(_race(target, concurrency, method))
        except Exception as e:
            return ToolResult(tool_name=self.name, target=target, success=False, error=str(e))

        unique_codes = set(codes)
        findings = []
        if len(unique_codes) > 1 or (200 in codes and codes.count(200) > 1):
            findings.append({
                "type": "race_condition",
                "severity": "HIGH",
                "detail": f"Non-deterministic responses: {dict((c, codes.count(c)) for c in unique_codes)}",
                "concurrency": concurrency,
            })

        return ToolResult(
            tool_name=self.name, target=target,
            success=True, findings=findings,
            raw_output=f"Sent {concurrency} concurrent {method} requests. Status codes: {dict((c, codes.count(c)) for c in unique_codes)}"
        )
