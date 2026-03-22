#!/usr/bin/env python3
"""NeuroRift tool: SQL Injection testing (sqlmap integration + custom payloads)."""

import subprocess
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["target"],
    "properties": {
        "target": {"type": "string", "description": "URL to test for SQL injection"},
        "level": {"type": "integer", "description": "sqlmap level 1-5", "default": 1},
        "risk": {"type": "integer", "description": "sqlmap risk 1-3", "default": 1},
    },
}


class SQLiTool:
    name = "sqli"
    description = (
        "Test a URL for SQL injection vulnerabilities (error-based, blind, time-based)"
    )

    @staticmethod
    def schema():
        return SCHEMA

    def run(self, target: str, level: int = 1, risk: int = 1) -> ToolResult:
        """Run sqlmap against target URL with safe defaults."""
        cmd = [
            "sqlmap",
            "-u",
            target,
            "--batch",
            "--level",
            str(level),
            "--risk",
            str(risk),
            "--output-dir",
            "/tmp/nr_sqlmap",
            "--forms",
            "--crawl=2",
            "--timeout=15",
            "--retries=1",
            "--flush-session",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            output = result.stdout + result.stderr
            findings = []
            if "Parameter:" in output and (
                "VULNERABLE" in output or "injections were found" in output
            ):
                findings.append(
                    {
                        "type": "sqli",
                        "severity": "CRITICAL",
                        "detail": "SQLi confirmed by sqlmap",
                    }
                )
            return ToolResult(
                tool_name=self.name,
                target=target,
                success=result.returncode == 0,
                findings=findings,
                raw_output=output[:2000],
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name,
                target=target,
                success=False,
                error="sqlmap timeout",
            )
        except FileNotFoundError:
            return ToolResult(
                tool_name=self.name,
                target=target,
                success=False,
                error="sqlmap not installed",
            )
