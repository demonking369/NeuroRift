"""Ollama model capability verification for autonomous NeuroRift agent mode."""

from __future__ import annotations

import json
import subprocess
from typing import Any

CAPABILITY_PROMPT = """Evaluate whether you can reliably perform the following tasks:

* structured tool invocation
* Linux command generation
* file creation and modification
* interpreting tool outputs
* multi-step reasoning for autonomous agents

Return a JSON response:
{
"tool_usage": true/false,
"command_generation": true/false,
"filesystem_operations": true/false,
"multi_step_reasoning": true/false,
"agent_ready": true/false
}"""


def _extract_json(raw_text: str) -> dict[str, Any]:
    raw_text = (raw_text or "").strip()
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    return json.loads(raw_text[start : end + 1])


def verify_model_capabilities(model_name: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["ollama", "run", model_name, CAPABILITY_PROMPT],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "error": "ollama_missing", "agent_ready": False}
    except Exception as exc:  # defensive for unstable environments
        return {
            "ok": False,
            "error": f"ollama_exec_error:{type(exc).__name__}",
            "agent_ready": False,
        }

    if proc.returncode != 0:
        return {
            "ok": False,
            "error": f"ollama_returned_{proc.returncode}",
            "stderr": proc.stderr,
            "agent_ready": False,
        }

    try:
        parsed = _extract_json(proc.stdout)
    except Exception as exc:
        return {
            "ok": False,
            "error": f"invalid_capability_json:{type(exc).__name__}",
            "raw": proc.stdout[:1000],
            "agent_ready": False,
        }

    required = {
        "tool_usage",
        "command_generation",
        "filesystem_operations",
        "multi_step_reasoning",
        "agent_ready",
    }
    if not required.issubset(parsed):
        return {
            "ok": False,
            "error": "capability_fields_missing",
            "parsed": parsed,
            "agent_ready": False,
        }

    parsed["ok"] = bool(parsed.get("agent_ready"))
    return parsed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Check Ollama model capability for NeuroRift agent mode"
    )
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    print(json.dumps(verify_model_capabilities(args.model), indent=2))
