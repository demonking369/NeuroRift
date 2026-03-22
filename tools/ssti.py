#!/usr/bin/env python3
"""NeuroRift tool: SSTI (Server-Side Template Injection) detection."""

import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "URL endpoint to test for SSTI"},
        "param": {"type": "string", "description": "Parameter to inject into", "default": "q"},
    }
}

# Engine-specific probes: payload, expected_fragment
SSTI_PROBES = [
    ("{{7*7}}", "49"),          # Jinja2, Twig
    ("${7*7}", "49"),           # FreeMarker, EL
    ("<%=7*7%>", "49"),         # ERB
    ("{{7*'7'}}", "7777777"),   # Jinja2 string multiplication
    ("#{7*7}", "49"),           # Pebble, Groovy
]


class SSTITool:
    name = "ssti"
    description = "Detect Server-Side Template Injection for Jinja2, Twig, FreeMarker, ERB"

    @staticmethod
    def schema(): return SCHEMA

    def run(self, target: str, param: str = "q") -> ToolResult:
        findings = []
        for payload, expected in SSTI_PROBES:
            try:
                resp = requests.get(target, params={param: payload}, timeout=10, verify=False)
                if expected in resp.text:
                    findings.append({
                        "type": "ssti",
                        "severity": "CRITICAL",
                        "payload": payload,
                        "expected": expected,
                        "param": param,
                        "url": resp.url,
                    })
            except requests.RequestException:
                continue
        return ToolResult(
            tool_name=self.name, target=target,
            success=True, findings=findings,
            raw_output=f"Tested {len(SSTI_PROBES)} SSTI payloads"
        )
