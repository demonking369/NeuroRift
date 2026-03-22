#!/usr/bin/env python3
"""Loads and validates notifications.yaml configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
DEFAULT_CONFIG_PATHS = [
    Path("config/notifications.yaml"),
    Path("notifications.yaml"),
]


class NotificationConfig:
    """Parsed, validated notification configuration."""

    def __init__(
        self,
        enabled: bool,
        gateway_url: str,
        enabled_channels: Dict[str, Dict[str, Any]],
        enabled_events: Set[str],
        min_severity: str,
    ) -> None:
        self.enabled = enabled
        self.gateway_url = gateway_url
        self.enabled_channels = enabled_channels
        self.enabled_events = enabled_events
        self.min_severity = min_severity
        self._min_severity_rank = SEVERITY_ORDER.get(min_severity, 1)

    def should_notify(self, event_type: str, severity: Optional[str] = None) -> bool:
        """Check if a notification should be sent for this event+severity."""
        if not self.enabled:
            return False

        # Critical findings ALWAYS send, regardless of filter
        if event_type == "critical_finding":
            return True

        # Check event toggle
        if event_type not in self.enabled_events:
            return False

        # Check severity filter for vulnerability events
        if severity and event_type == "vulnerability_found":
            sev_rank = SEVERITY_ORDER.get(severity.lower(), 0)
            if sev_rank < self._min_severity_rank:
                return False

        return True

    def get_active_channels(self) -> List[str]:
        """Return list of enabled channel names."""
        return list(self.enabled_channels.keys())


def load_config(config_path: Optional[str] = None) -> NotificationConfig:
    """Load notification config from YAML file.

    Args:
        config_path: Explicit path to config file. If None, searches default locations.

    Returns:
        NotificationConfig with validated settings.
    """
    path = _resolve_config_path(config_path)

    if path is None:
        logger.info("No notifications.yaml found — notifications disabled")
        return NotificationConfig(
            enabled=False,
            gateway_url="ws://127.0.0.1:18789",
            enabled_channels={},
            enabled_events=set(),
            min_severity="medium",
        )

    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.warning("Failed to read %s: %s — notifications disabled", path, exc)
        return NotificationConfig(
            enabled=False,
            gateway_url="ws://127.0.0.1:18789",
            enabled_channels={},
            enabled_events=set(),
            min_severity="medium",
        )

    cfg = raw.get("notifications", raw)

    # Parse channels
    channels_raw = cfg.get("channels", {})
    enabled_channels: Dict[str, Dict[str, Any]] = {}
    for name, ch_cfg in channels_raw.items():
        if isinstance(ch_cfg, dict) and ch_cfg.get("enabled", False):
            enabled_channels[name] = ch_cfg

    # Parse events
    events_raw = cfg.get("events", {})
    enabled_events: Set[str] = set()
    for event_name, is_enabled in events_raw.items():
        if is_enabled:
            enabled_events.add(event_name)

    return NotificationConfig(
        enabled=cfg.get("enabled", True),
        gateway_url=cfg.get("openclaw_gateway", "ws://127.0.0.1:18789"),
        enabled_channels=enabled_channels,
        enabled_events=enabled_events,
        min_severity=cfg.get("min_severity", "medium"),
    )


def _resolve_config_path(explicit: Optional[str] = None) -> Optional[Path]:
    """Find the notifications config file."""
    if explicit:
        p = Path(explicit)
        return p if p.is_file() else None

    for candidate in DEFAULT_CONFIG_PATHS:
        if candidate.is_file():
            return candidate

    return None
