#!/usr/bin/env python3
"""NeuroRift v2 — AI Executor: dispatches AI tool calls, loops until stop condition."""

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional

import neurocore

logger = logging.getLogger(__name__)

with open("ai/prompts/executor_system.txt") as _f:
    EXECUTOR_SYSTEM = _f.read()

MAX_ITERATIONS = 20  # Safety cap: never loop forever


class Executor:
    def __init__(self, tool_registry: Dict[str, Callable], dispatcher: Any = None):
        """
        Args:
            tool_registry: dict mapping tool_name -> callable(target, **args) -> dict
            dispatcher: Optional NotificationDispatcher for scan event notifications
        """
        self.tools = tool_registry
        self.dispatcher = dispatcher
        self._tool_schemas = [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": fn.__doc__ or name,
                    "parameters": getattr(fn, "schema", lambda: {})(),
                },
            }
            for name, fn in tool_registry.items()
        ]

    async def run(self, plan: List[Any], session_state: Any) -> List[Dict[str, Any]]:
        """
        Execute the attack plan via Manus-style autonomous while loop.
        Loop exits when model outputs TASK_COMPLETE or max iterations reached.
        """
        findings: List[Dict[str, Any]] = []
        history = [{"role": "system", "content": EXECUTOR_SYSTEM}]

        # Seed with the plan
        plan_text = json.dumps(
            [
                {
                    "tool": s.tool_name,
                    "target": s.target,
                    "args": s.args,
                    "reason": s.reasoning,
                }
                for s in plan
            ],
            indent=2,
        )
        history.append(
            {
                "role": "user",
                "content": f"Execute this plan:\n```json\n{plan_text}\n```",
            }
        )

        for iteration in range(MAX_ITERATIONS):
            neurocore.load_model("tool_calling")
            response = neurocore.infer(
                history, tools=self._tool_schemas, temperature=0.1
            )
            neurocore.unload_model()

            if not response or response.get("error"):
                logger.error(
                    "Executor LLM call failed on iteration %d: %s", iteration, response
                )
                break

            if response["type"] == "text":
                content = response["content"]
                history.append({"role": "assistant", "content": content})

                # Stop condition
                if "TASK_COMPLETE" in content:
                    logger.info(
                        "Executor reached TASK_COMPLETE on iteration %d", iteration
                    )
                    break

            elif response["type"] == "tool_calls":
                history.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": response["calls"],
                    }
                )

                for call in response["calls"]:
                    fn_name = call.get("function", {}).get("name", "")
                    fn_args = json.loads(
                        call.get("function", {}).get("arguments", "{}")
                    )
                    call_id = call.get("id", "")

                    result = await self._dispatch(fn_name, fn_args, session_state)
                    findings.append(
                        {"tool": fn_name, "args": fn_args, "result": result}
                    )

                    # Notify on vulnerability findings
                    self._notify_finding(fn_name, fn_args, result)

                    # Feed result back to model
                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": json.dumps(result),
                        }
                    )

        return findings

    def _notify_finding(
        self, tool_name: str, args: Dict, result: Dict[str, Any]
    ) -> None:
        """Send notification if a vulnerability was found."""
        if not self.dispatcher:
            return

        # Skip if result is an error or has no findings
        if result.get("error") or not result.get("vulnerable", False):
            return

        severity = result.get("severity", "medium")
        vuln_data = {
            "vuln_type": tool_name,
            "affected_url": args.get("target", args.get("url", "N/A")),
            "parameter": args.get("parameter", "N/A"),
            "severity": severity,
            "confidence": result.get("confidence", "N/A"),
            "cvss_score": result.get("cvss", "N/A"),
        }

        # Always send critical findings separately
        if severity.lower() == "critical":
            vuln_data["impact_summary"] = result.get("impact", "Critical vulnerability detected")
            vuln_data["evidence_snippet"] = str(result.get("evidence", ""))[:200]
            self.dispatcher.send("critical_finding", vuln_data)
        else:
            self.dispatcher.send("vulnerability_found", vuln_data)

    async def _dispatch(
        self, tool_name: str, args: Dict, session_state: Any
    ) -> Dict[str, Any]:
        """Call registered tool, save result to session, return structured output."""
        fn = self.tools.get(tool_name)
        if not fn:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            result = fn(**args)
            if hasattr(result, "to_dict"):
                result_dict = result.to_dict()
            elif hasattr(result, "__dict__"):
                result_dict = vars(result)
            else:
                result_dict = result

            session_state.save_tool_result(tool_name, args, result_dict)
            return result_dict
        except Exception as e:
            logger.error("Tool %s failed: %s", tool_name, e)
            return {"error": str(e)}
