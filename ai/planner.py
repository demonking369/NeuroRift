#!/usr/bin/env python3
"""NeuroRift v2 — AI Planner: takes compressed recon JSON, outputs ordered attack plan."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

from ai.llama_client import LlamaClient

logger = logging.getLogger(__name__)


@dataclass
class AttackStep:
    tool_name: str
    target: str
    args: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


PLANNER_SYSTEM = open("ai/prompts/planner_system.txt").read()


class Planner:
    def __init__(self, client: LlamaClient):
        self.client = client

    async def create_plan(self, recon_summary: str, available_tools: List[Dict], scope_map: Any) -> List[AttackStep]:
        """
        Generate an ordered attack plan from compressed recon data.
        Enforces 500-token budget on recon_summary input.
        """
        # Hard cap: never feed more than ~500 tokens (~2000 chars) to model
        if len(recon_summary) > 2000:
            recon_summary = recon_summary[:2000] + "\n[TRUNCATED — see session state for full recon]"

        tools_desc = "\n".join(
            f"- {t['name']}: {t['description']}" for t in available_tools
        )
        scope_str = str(scope_map)

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": (
                f"RECON DATA:\n{recon_summary}\n\n"
                f"SCOPE:\n{scope_str}\n\n"
                f"AVAILABLE TOOLS:\n{tools_desc}\n\n"
                "Output a JSON attack plan array."
            )},
        ]

        response = await self.client.generate_chat(messages, temperature=0.1)
        if not response or response.get("error"):
            logger.error("Planner LLM call failed: %s", response)
            return []

        raw = response.get("content", "")
        try:
            match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", raw)
            cleaned = match.group(0) if match else raw.replace("```json", "").replace("```", "").strip()
            steps_data = json.loads(cleaned)
            return [
                AttackStep(
                    tool_name=s.get("tool_name", ""),
                    target=s.get("target", ""),
                    args=s.get("args", {}),
                    reasoning=s.get("reasoning", ""),
                )
                for s in steps_data
                if s.get("tool_name")
            ]
        except Exception as e:
            logger.error("Failed to parse planner output: %s\nRaw: %s", e, raw[:500])
            return []
