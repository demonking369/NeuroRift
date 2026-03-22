#!/usr/bin/env python3
"""
NeuroRift v2 — tools/__init__.py
Base class for all AI-callable tools. Scope enforcer runs before every tool.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    tool_name: str
    target: str
    success: bool
    findings: List[Dict[str, Any]] = field(default_factory=list)
    raw_output: str = ""
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)
