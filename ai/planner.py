#!/usr/bin/env python3
"""NeuroRift v2 — AI Planner: takes compressed recon JSON, outputs ordered attack plan."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

import neurocore

logger = logging.getLogger(__name__)


@dataclass
class AttackStep:
    tool_name: str
    target: str
    args: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


with open("ai/prompts/planner_system.txt") as _f:
    PLANNER_SYSTEM = _f.read()


class Planner:
    def __init__(self):
        pass

    @staticmethod
    def create_plan(
        recon_summary: str, available_tools: List[Dict], scope_map: Any
    ) -> List[AttackStep]:
        """
        Generate an ordered attack plan from compressed recon data.
        Enforces 500-token budget on recon_summary input.
        """
        # Hard cap: never feed more than ~500 tokens (~2000 chars) to model
        if len(recon_summary) > 2000:
            recon_summary = (
                recon_summary[:2000]
                + "\n[TRUNCATED — see session state for full recon]"
            )

        tools_desc = "\n".join(
            f"- {t['name']}: {t['description']}" for t in available_tools
        )
        scope_str = str(scope_map)

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"RECON DATA:\n{recon_summary}\n\n"
                    f"SCOPE:\n{scope_str}\n\n"
                    f"AVAILABLE TOOLS:\n{tools_desc}\n\n"
                    "Output a JSON attack plan array."
                ),
            },
        ]

        neurocore.load_model("vuln_planning")
        response = neurocore.infer(messages, tools=available_tools, temperature=0.1)
        neurocore.unload_model()

        if not response:
            logger.error("Planner LLM call returned empty")
            return []

        if isinstance(response, dict) and response.get("error"):
            logger.error("Planner LLM call failed: %s", response)
            return []

        if isinstance(response, list):
            steps_data = response
        else:
            raw = (
                response.get("content", str(response))
                if isinstance(response, dict)
                else str(response)
            )
            try:
                match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", raw)
                cleaned = (
                    match.group(0)
                    if match
                    else raw.replace("```json", "").replace("```", "").strip()
                )
                steps_data = json.loads(cleaned)
            except Exception as e:
                logger.error(
                    "Failed to parse planner output: %s\nRaw: %s", e, raw[:500]
                )
                return []

        return [
            AttackStep(
                tool_name=s.get("tool_name", ""),
                target=s.get("target", ""),
                args=s.get("args", {}),
                reasoning=s.get("reasoning", ""),
            )
            for s in steps_data
            if isinstance(s, dict) and s.get("tool_name")
        ]
