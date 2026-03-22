"""Runtime environment verification for NeuroRift startup."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REQUIRED_TOOLS = ("python3", "curl", "nmap")


def check_tool(tool: str) -> dict:
    resolved = shutil.which(tool)
    if not resolved:
        return {
            "tool": tool,
            "ok": False,
            "error": "missing",
            "install_hint": f"Install {tool} using your package manager (e.g., sudo apt install {tool}).",
        }

    if not os.access(resolved, os.X_OK):
        return {
            "tool": tool,
            "ok": False,
            "error": "not_executable",
            "install_hint": f"Grant execute permission: chmod +x {resolved}",
        }

    try:
        probe = subprocess.run(
            [tool, "--help"], capture_output=True, text=True, timeout=8, check=False
        )
        if probe.returncode not in (0, 1, 2):
            return {
                "tool": tool,
                "ok": False,
                "error": f"probe_failed_exit_{probe.returncode}",
                "install_hint": f"Reinstall or verify {tool} works from shell.",
            }
    except Exception as exc:  # defensive startup guard
        return {
            "tool": tool,
            "ok": False,
            "error": f"probe_exception:{type(exc).__name__}",
            "install_hint": f"Verify {tool} manually: {tool} --help",
        }

    return {"tool": tool, "ok": True, "path": resolved}


def verify_runtime_environment(workdir: Path | None = None) -> dict:
    workdir = workdir or (Path.home() / ".neurorift")
    workdir.mkdir(parents=True, exist_ok=True)

    checks = [check_tool(tool) for tool in REQUIRED_TOOLS]
    all_ok = all(c["ok"] for c in checks)

    return {
        "ok": all_ok,
        "workdir": str(workdir),
        "tools": checks,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(verify_runtime_environment(), indent=2))
