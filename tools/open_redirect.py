#!/usr/bin/env python3
"""NeuroRift tool: Open Redirect detection."""

import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "URL endpoint to test for open redirect"},
        "param": {"type": "string", "description": "Redirect parameter name", "default": "redirect"},
    }
}

REDIRECT_PAYLOADS = [
    "//evil.com", "https://evil.com", "/\\evil.com",
    "https:evil.com", "//evil.com/%2f..", "%0d%0ahttps://evil.com",
]


class OpenRedirectTool:
    name = "open_redirect"
    description = "Detect open redirect vulnerabilities for SSRF escalation"

    @staticmethod
    def schema(): return SCHEMA

    def run(self, target: str, param: str = "redirect") -> ToolResult:
        findings = []
        for payload in REDIRECT_PAYLOADS:
            try:
                resp = requests.get(
                    target, params={param: payload},
                    timeout=8, verify=False, allow_redirects=False
                )
                if resp.status_code in (301, 302, 307, 308):
                    location = resp.headers.get("Location", "")
                    if "evil.com" in location or location.startswith("//"):
                        findings.append({
                            "type": "open_redirect",
                            "severity": "MEDIUM",
                            "payload": payload,
                            "location": location,
                            "param": param,
                        })
            except requests.RequestException:
                continue
        return ToolResult(
            tool_name=self.name, target=target,
            success=True, findings=findings,
            raw_output=f"Tested {len(REDIRECT_PAYLOADS)} redirect payloads"
        )
