#!/usr/bin/env python3
"""NeuroRift v2 — Context compressor. Keeps model input under 500 tokens."""

import json
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from session.state import SessionState, ToolOutput

MAX_CHARS = 2000  # ~500 tokens
KEEP_LAST_N = 3


class Compressor:
    """
    Compresses session state for AI model consumption.
    Hard limit: never exceed ~500 tokens (2000 chars) of recon data per call.
    Strategy: keep last 3 tool results + truncated summary of earlier results.
    """

    def compress(self, state: "SessionState") -> str:
        outputs: List["ToolOutput"] = state.tool_outputs
        findings = state.findings

        # Build a brief header
        header = f"Session: {state.session_id} | Tools run: {len(outputs)} | Findings: {len(findings)}\n"

        # Summarize earlier results as short single-line entries
        earlier = outputs[:-KEEP_LAST_N] if len(outputs) > KEEP_LAST_N else []
        recent = outputs[-KEEP_LAST_N:] if outputs else []

        summary_lines = [f"[earlier] {o.tool_name}({o.target}): {self._brief(o.result)}" for o in earlier]
        recent_blocks = []
        for o in recent:
            block = f"[{o.tool_name} → {o.target}]\n{json.dumps(o.result, indent=2)[:500]}"
            recent_blocks.append(block)

        # Compose and truncate
        summary_str = "\n".join(summary_lines)
        recent_str = "\n---\n".join(recent_blocks)
        findings_str = "\n".join(
            f"[{f.severity}] {f.title}: {f.affected_url}" for f in findings[-5:]
        )
        findings_block = f"\nFINDINGS SO FAR:\n{findings_str}" if findings else "\nFINDINGS SO FAR:\nNone"
        
        # Calculate budget for recon data
        budget = MAX_CHARS - len(header) - len(findings_block) - 50 # 50 chars safety margin
        
        recon_data = f"SUMMARY:\n{summary_str}\n\nRECENT RESULTS:\n{recent_str}"
        if len(recon_data) > budget:
            recon_data = recon_data[:budget] + "\n...[TRUNCATED RECON DATA]"

        full = f"{header}\n{recon_data}\n{findings_block}"
        return full

    @staticmethod
    def _brief(result: dict) -> str:
        """One-line summary of a tool result."""
        if "error" in result:
            return f"ERROR: {result['error']}"
        keys = list(result.keys())[:3]
        return ", ".join(f"{k}={result[k]!r}" for k in keys)
