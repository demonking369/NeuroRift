#!/usr/bin/env python3
"""NeuroRift tool: IDOR (Insecure Direct Object Reference) testing."""

import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "Base URL with an ID parameter, e.g. https://api.example.com/users/1"},
        "id_range": {"type": "integer", "description": "Number of sequential IDs to probe", "default": 5},
        "session_cookie": {"type": "string", "description": "Auth session cookie for context", "default": ""},
    }
}


class IDORTool:
    name = "idor"
    description = "Probe sequential object IDs to detect unauthorized access (IDOR)"

    @staticmethod
    def schema(): return SCHEMA

    def run(self, target: str, id_range: int = 5, session_cookie: str = "") -> ToolResult:
        headers = {}
        cookies = {}
        if session_cookie:
            cookies["session"] = session_cookie

        findings = []
        base = target.rstrip("/")
        # Extract base without trailing ID
        import re
        base_match = re.split(r'/(\d+)$', base)
        base_url = base_match[0] if len(base_match) > 1 else base
        start_id = int(base_match[1]) if len(base_match) > 1 else 1

        for i in range(start_id, start_id + id_range):
            url = f"{base_url}/{i}"
            try:
                resp = requests.get(url, headers=headers, cookies=cookies, timeout=10, verify=False)
                if resp.status_code == 200 and len(resp.text) > 50:
                    findings.append({
                        "type": "idor",
                        "severity": "HIGH",
                        "url": url,
                        "status": resp.status_code,
                        "response_length": len(resp.text),
                    })
            except requests.RequestException:
                continue

        return ToolResult(
            tool_name=self.name, target=target,
            success=True, findings=findings,
            raw_output=f"Probed IDs {start_id} to {start_id + id_range - 1}"
        )
