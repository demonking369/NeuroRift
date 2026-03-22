#!/usr/bin/env python3
"""Notification message templates for NeuroRift scan events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class NotificationMessage:
    """Rendered notification ready to send."""
    event_type: str
    title: str
    body: str
    severity: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(tz=timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────
# Template definitions
# ──────────────────────────────────────────────────────────────

TEMPLATES: Dict[str, Dict[str, str]] = {
    "scan_started": {
        "title": "🎯 NeuroRift Scan Started",
        "body": (
            "Target: {target_url}\n"
            "Scope: {scope_name}\n"
            "Time: {timestamp}"
        ),
    },
    "recon_complete": {
        "title": "🔍 Recon Complete",
        "body": (
            "Target: {target_url}\n"
            "Subdomains found: {subdomain_count}\n"
            "Endpoints found: {endpoint_count}\n"
            "Technologies: {tech_stack}\n"
            "Starting vuln scan..."
        ),
    },
    "vulnerability_found": {
        "title": "🚨 Vulnerability Found [{severity}]",
        "body": (
            "Type: {vuln_type}\n"
            "URL: {affected_url}\n"
            "Parameter: {parameter}\n"
            "Confidence: {confidence}%\n"
            "CVSS: {cvss_score}"
        ),
    },
    "critical_finding": {
        "title": "🔴 CRITICAL FINDING",
        "body": (
            "Type: {vuln_type}\n"
            "Target: {affected_url}\n"
            "Impact: {impact_summary}\n"
            "Evidence: {evidence_snippet}\n"
            "Full report generating..."
        ),
    },
    "scan_complete": {
        "title": "✅ Scan Complete",
        "body": (
            "Target: {target_url}\n"
            "Duration: {scan_duration}\n"
            "Findings: {total_findings}\n"
            "Critical: {critical_count}\n"
            "High: {high_count}\n"
            "Medium: {medium_count}\n"
            "Report saved: {report_path}"
        ),
    },
    "scan_failed": {
        "title": "❌ Scan Failed",
        "body": (
            "Target: {target_url}\n"
            "Error: {error_message}\n"
            "Stage: {failed_stage}"
        ),
    },
    "model_loaded": {
        "title": "🧠 Model Loaded",
        "body": (
            "Model: {model_name}\n"
            "Role: {role}\n"
            "VRAM: {vram_usage_mb}MB"
        ),
    },
}


def render(event_type: str, data: Dict[str, Any]) -> NotificationMessage:
    """Render a notification message from an event type and data dict.

    Args:
        event_type: One of the TEMPLATES keys (e.g. 'scan_started').
        data: Dict of template variables. Missing keys produce 'N/A'.

    Returns:
        NotificationMessage ready to send.
    """
    template = TEMPLATES.get(event_type)
    if template is None:
        return NotificationMessage(
            event_type=event_type,
            title=f"📢 {event_type}",
            body=str(data),
        )

    # Safe formatting: missing keys become 'N/A'
    safe_data = _SafeDict(data)
    safe_data.setdefault("timestamp", datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))

    title = template["title"].format_map(safe_data)
    body = template["body"].format_map(safe_data)

    return NotificationMessage(
        event_type=event_type,
        title=title,
        body=body,
        severity=data.get("severity"),
    )


class _SafeDict(dict):
    """Dict subclass that returns 'N/A' for missing keys during format_map."""

    def __missing__(self, key: str) -> str:
        return "N/A"
