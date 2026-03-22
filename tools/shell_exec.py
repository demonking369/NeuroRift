#!/usr/bin/env python3
"""
NeuroRift tool: Sandboxed shell command execution.
STRICT WHITELIST — never allows destructive commands.
"""

import subprocess
import shutil
from tools import ToolResult

SCHEMA = {
    "type": "object",
    "required": ["command"],
    "properties": {
        "command": {"type": "string", "description": "Shell command to run (must use a whitelisted tool)"},
        "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60},
    }
}

ALLOWED_BINARIES = frozenset([
    "nmap", "subfinder", "ffuf", "nuclei", "whatweb",
    "sqlmap", "curl", "dig", "nslookup", "whois",
])

BLOCKED_KEYWORDS = frozenset([
    "rm", "dd", "mkfs", "format", "shred", "fdisk",
    ">", ">>", "chmod", "chown", "sudo", "su", "bash", "sh",
    "python", "perl", "ruby", "wget", "nc", "netcat",
    "/etc/passwd", "/etc/shadow",
])


class ShellExecTool:
    name = "shell_exec"
    description = "Execute external security tools from the whitelist in a sandboxed manner"

    @staticmethod
    def schema(): return SCHEMA

    def run(self, command: str, timeout: int = 60) -> ToolResult:
        # Validate binary is whitelisted
        parts = command.split()
        if not parts:
            return ToolResult(tool_name=self.name, target="", success=False, error="Empty command")

        binary = parts[0]
        if binary not in ALLOWED_BINARIES:
            return ToolResult(
                tool_name=self.name, target="", success=False,
                error=f"Binary '{binary}' is not in the whitelist. Allowed: {sorted(ALLOWED_BINARIES)}"
            )

        # Check for blocked keywords
        for blocked in BLOCKED_KEYWORDS:
            if blocked in command:
                return ToolResult(
                    tool_name=self.name, target="", success=False,
                    error=f"Blocked keyword '{blocked}' detected in command. Command rejected."
                )

        # Check binary is actually installed
        if not shutil.which(binary):
            return ToolResult(
                tool_name=self.name, target="", success=False,
                error=f"Binary '{binary}' is not installed. Run scripts/install_deps.sh"
            )

        try:
            result = subprocess.run(
                command, shell=False, args=parts,
                capture_output=True, text=True, timeout=timeout
            )
            return ToolResult(
                tool_name=self.name, target=binary,
                success=result.returncode == 0,
                raw_output=(result.stdout + result.stderr)[:5000],
                error=result.stderr[:500] if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool_name=self.name, target=binary, success=False,
                error=f"Command timed out after {timeout}s"
            )
