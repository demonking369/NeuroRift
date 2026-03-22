"""llama.cpp model capability verification for autonomous NeuroRift agent mode."""

from __future__ import annotations

import json
import asyncio
from typing import Any
from ai_wrapper.llama_client import LlamaClient

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


async def _verify_async(model_name: str) -> dict[str, Any]:
    client = LlamaClient()
    try:
        messages = [{"role": "user", "content": CAPABILITY_PROMPT}]
        res = await client.generate_chat(messages, model=model_name)
        if not res or res.get("type") != "text":
            return {
                "ok": False,
                "error": "llama_exec_error:invalid_response",
                "agent_ready": False,
            }

        parsed = _extract_json(res.get("content", ""))
    except Exception as exc:  # defensive for unstable environments
        return {
            "ok": False,
            "error": f"llama_exec_error:{type(exc).__name__}",
            "agent_ready": False,
        }

    required = {
        "tool_usage",
        "command_generation",
        "filesystem_operations",
        "multi_step_reasoning",
        "agent_ready",
    }
    if not required.issubset(parsed.keys()):
        return {
            "ok": False,
            "error": "capability_fields_missing",
            "parsed": parsed,
            "agent_ready": False,
        }

    parsed["ok"] = bool(parsed.get("agent_ready"))
    return parsed


def verify_model_capabilities(model_name: str) -> dict[str, Any]:
    return asyncio.run(_verify_async(model_name))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Check llama.cpp model capability for NeuroRift agent mode"
    )
    parser.add_argument("--model", required=True)
    args = parser.parse_args()
    print(json.dumps(verify_model_capabilities(args.model), indent=2))
