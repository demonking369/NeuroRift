#!/usr/bin/env python3
"""NeuroRift v2 — Session state. Persists all findings and tool outputs to disk."""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolOutput:
    tool_name: str
    target: str
    args: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Finding:
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    description: str
    affected_url: str
    evidence: str = ""
    remediation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SessionState:
    def __init__(self, session_id: str, output_dir: str = "session/logs"):
        self.session_id = session_id
        self.output_dir = Path(output_dir) / session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.output_dir / "state.json"

        self.tool_outputs: List[ToolOutput] = []
        self.findings: List[Finding] = []
        self.metadata: Dict[str, Any] = {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Resume from existing state if present
        if self.state_file.exists():
            self._load()
            logger.info("Resumed session %s", session_id)
        else:
            self._save()

    def save_tool_result(
        self, tool_name: str, args: Dict, result: Dict, target: str = ""
    ) -> None:
        """Persist tool output to disk immediately after execution."""
        output = ToolOutput(
            tool_name=tool_name, target=target, args=args, result=result
        )
        self.tool_outputs.append(output)
        self._save()

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)
        self._save()

    def _save(self) -> None:
        state = {
            "metadata": self.metadata,
            "tool_outputs": [asdict(o) for o in self.tool_outputs],
            "findings": [asdict(f) for f in self.findings],
        }
        try:
            self.state_file.write_text(
                json.dumps(state, indent=2, default=str), encoding="utf-8"
            )
        except OSError as e:
            logger.error("Failed to save session state: %s", e)

    def _load(self) -> None:
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            self.metadata = data.get("metadata", self.metadata)
            self.tool_outputs = [ToolOutput(**o) for o in data.get("tool_outputs", [])]
            self.findings = [Finding(**f) for f in data.get("findings", [])]
        except (json.JSONDecodeError, TypeError) as e:
            logger.error("Corrupted session state — starting fresh: %s", e)
