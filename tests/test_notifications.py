#!/usr/bin/env python3
"""Tests for the NeuroRift notification system.

Tests cover:
- Config loading and validation
- Template rendering for all event types
- Severity filtering and event toggles
- Dispatcher queue behavior
- Graceful failure when gateway offline
- Retry logic
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Module imports
from notifications.config_loader import NotificationConfig, load_config
from notifications.templates import render, TEMPLATES, _SafeDict
from notifications.dispatcher import NotificationDispatcher


# ─── Config Loading Tests ────────────────────────────────────────


class TestConfigLoader:
    def test_load_config_from_valid_yaml(self, tmp_path):
        """Test loading a valid notifications.yaml."""
        config_file = tmp_path / "notifications.yaml"
        config_file.write_text("""
notifications:
  enabled: true
  openclaw_gateway: ws://127.0.0.1:18789
  channels:
    discord:
      enabled: true
      token: "test-token"
      channel_id: "12345"
    telegram:
      enabled: false
      bot_token: ""
      chat_id: ""
  events:
    scan_started: true
    vulnerability_found: true
    scan_complete: true
    model_loaded: false
  min_severity: high
""")
        config = load_config(str(config_file))
        assert config.enabled is True
        assert config.gateway_url == "ws://127.0.0.1:18789"
        assert "discord" in config.enabled_channels
        assert "telegram" not in config.enabled_channels
        assert "scan_started" in config.enabled_events
        assert "model_loaded" not in config.enabled_events
        assert config.min_severity == "high"

    def test_load_config_missing_file_returns_disabled(self):
        """Test graceful handling when config file doesn't exist."""
        config = load_config("/tmp/nonexistent_notifications.yaml")
        assert config.enabled is False
        assert config.enabled_channels == {}
        assert config.enabled_events == set()

    def test_load_config_empty_yaml_returns_defaults(self, tmp_path):
        """Test loading an empty YAML file — defaults to enabled with no channels."""
        config_file = tmp_path / "notifications.yaml"
        config_file.write_text("")
        config = load_config(str(config_file))
        assert config.enabled is True
        assert config.enabled_channels == {}
        assert config.min_severity == "medium"

    def test_disabled_channels_are_excluded(self, tmp_path):
        """Test that disabled channels don't appear in enabled_channels."""
        config_file = tmp_path / "notifications.yaml"
        config_file.write_text("""
notifications:
  enabled: true
  channels:
    discord:
      enabled: false
      token: ""
    slack:
      enabled: true
      bot_token: "xoxb-test"
      channel: "#alerts"
  events:
    scan_started: true
  min_severity: medium
""")
        config = load_config(str(config_file))
        assert "discord" not in config.enabled_channels
        assert "slack" in config.enabled_channels


# ─── Severity Filtering Tests ────────────────────────────────────


class TestSeverityFilter:
    def _make_config(self, min_severity="medium"):
        return NotificationConfig(
            enabled=True,
            gateway_url="ws://localhost:18789",
            enabled_channels={"discord": {"enabled": True}},
            enabled_events={"vulnerability_found", "critical_finding", "scan_complete"},
            min_severity=min_severity,
        )

    def test_severity_filter_blocks_low(self):
        """Test that low severity findings are blocked when min=medium."""
        config = self._make_config("medium")
        assert config.should_notify("vulnerability_found", "low") is False

    def test_severity_filter_allows_medium(self):
        """Test that medium severity findings pass when min=medium."""
        config = self._make_config("medium")
        assert config.should_notify("vulnerability_found", "medium") is True

    def test_severity_filter_allows_high(self):
        """Test that high severity findings pass when min=medium."""
        config = self._make_config("medium")
        assert config.should_notify("vulnerability_found", "high") is True

    def test_severity_filter_allows_critical(self):
        """Test that critical severity findings pass regardless."""
        config = self._make_config("high")
        assert config.should_notify("vulnerability_found", "critical") is True

    def test_critical_finding_always_sends(self):
        """Critical finding event type always sends regardless of filter."""
        config = self._make_config("critical")
        assert config.should_notify("critical_finding", "low") is True

    def test_disabled_event_is_blocked(self):
        """Events not in enabled_events are blocked."""
        config = self._make_config("low")
        assert config.should_notify("model_loaded") is False

    def test_disabled_config_blocks_all(self):
        """When enabled=False, nothing sends."""
        config = NotificationConfig(
            enabled=False,
            gateway_url="ws://localhost:18789",
            enabled_channels={"discord": {"enabled": True}},
            enabled_events={"scan_started"},
            min_severity="low",
        )
        assert config.should_notify("scan_started") is False


# ─── Template Rendering Tests ────────────────────────────────────


class TestTemplateRendering:
    def test_scan_started_template(self):
        """Test scan_started template renders correctly."""
        msg = render("scan_started", {
            "target_url": "https://example.com",
            "scope_name": "main-scope",
        })
        assert msg.event_type == "scan_started"
        assert "🎯" in msg.title
        assert "https://example.com" in msg.body
        assert "main-scope" in msg.body

    def test_vulnerability_found_template(self):
        """Test vulnerability_found template renders with severity."""
        msg = render("vulnerability_found", {
            "severity": "HIGH",
            "vuln_type": "SQL Injection",
            "affected_url": "https://example.com/login",
            "parameter": "username",
            "confidence": "95",
            "cvss_score": "8.9",
        })
        assert "HIGH" in msg.title
        assert "SQL Injection" in msg.body
        assert "username" in msg.body
        assert msg.severity == "HIGH"

    def test_critical_finding_template(self):
        """Test critical_finding template."""
        msg = render("critical_finding", {
            "vuln_type": "RCE",
            "affected_url": "https://example.com/api",
            "impact_summary": "Full server compromise",
            "evidence_snippet": "os.system('id')",
        })
        assert "🔴" in msg.title
        assert "RCE" in msg.body
        assert "Full server compromise" in msg.body

    def test_scan_complete_template(self):
        """Test scan_complete template with findings summary."""
        msg = render("scan_complete", {
            "target_url": "https://example.com",
            "scan_duration": "12m 34s",
            "total_findings": "15",
            "critical_count": "2",
            "high_count": "5",
            "medium_count": "8",
            "report_path": "/reports/report_20260322.md",
        })
        assert "✅" in msg.title
        assert "15" in msg.body
        assert "12m 34s" in msg.body

    def test_scan_failed_template(self):
        """Test scan_failed template with error details."""
        msg = render("scan_failed", {
            "target_url": "https://example.com",
            "error_message": "Connection timeout",
            "failed_stage": "recon",
        })
        assert "❌" in msg.title
        assert "Connection timeout" in msg.body
        assert "recon" in msg.body

    def test_missing_keys_render_as_na(self):
        """Test that missing template variables render as 'N/A'."""
        msg = render("vulnerability_found", {"severity": "HIGH"})
        assert "N/A" in msg.body  # missing parameter, url, etc.

    def test_unknown_event_type(self):
        """Test that unknown event types get a generic template."""
        msg = render("unknown_event", {"foo": "bar"})
        assert msg.event_type == "unknown_event"
        assert "📢" in msg.title

    def test_all_defined_templates_render(self):
        """Test that every defined template renders without error."""
        for event_type in TEMPLATES:
            msg = render(event_type, {})
            assert msg.event_type == event_type
            assert msg.title
            assert msg.body


# ─── SafeDict Tests ──────────────────────────────────────────────


class TestSafeDict:
    def test_missing_key_returns_na(self):
        d = _SafeDict({"a": "1"})
        assert d["a"] == "1"
        assert d["missing"] == "N/A"

    def test_format_map_with_missing(self):
        template = "Hello {name}, your {missing_field} is ready"
        result = template.format_map(_SafeDict({"name": "Arun"}))
        assert result == "Hello Arun, your N/A is ready"


# ─── Dispatcher Tests ────────────────────────────────────────────


class TestDispatcher:
    def _make_dispatcher(self, enabled=True, events=None, min_severity="medium"):
        """Create a dispatcher with mocked config."""
        config = NotificationConfig(
            enabled=enabled,
            gateway_url="ws://127.0.0.1:18789",
            enabled_channels={"discord": {"enabled": True}},
            enabled_events=events or {"scan_started", "vulnerability_found", "critical_finding", "scan_complete", "scan_failed"},
            min_severity=min_severity,
        )
        dispatcher = NotificationDispatcher.__new__(NotificationDispatcher)
        dispatcher.config = config
        dispatcher._queue = asyncio.Queue(maxsize=100)
        dispatcher._ws = None
        dispatcher._worker_task = None
        dispatcher._running = False
        dispatcher._session_id = "nr-notify-test1234"
        return dispatcher

    def test_send_queues_event(self):
        """Test that send() puts event into the queue."""
        dispatcher = self._make_dispatcher()
        dispatcher.send("scan_started", {"target_url": "https://example.com"})
        assert dispatcher._queue.qsize() == 1
        item = dispatcher._queue.get_nowait()
        assert item["event_type"] == "scan_started"

    def test_send_skips_disabled(self):
        """Test that send() is a no-op when notifications are disabled."""
        dispatcher = self._make_dispatcher(enabled=False)
        dispatcher.send("scan_started", {"target_url": "https://example.com"})
        assert dispatcher._queue.qsize() == 0

    def test_send_skips_unregistered_event(self):
        """Test that send() skips events not in enabled_events."""
        dispatcher = self._make_dispatcher(events={"scan_started"})
        dispatcher.send("model_loaded", {"model_name": "test"})
        assert dispatcher._queue.qsize() == 0

    def test_send_filters_low_severity(self):
        """Test that low severity findings are filtered out."""
        dispatcher = self._make_dispatcher(min_severity="high")
        dispatcher.send("vulnerability_found", {
            "severity": "low",
            "vuln_type": "info disclosure",
        })
        assert dispatcher._queue.qsize() == 0

    def test_send_allows_critical_regardless(self):
        """Test that critical_finding always sends regardless of filter."""
        dispatcher = self._make_dispatcher(min_severity="critical")
        dispatcher.send("critical_finding", {
            "severity": "low",
            "vuln_type": "RCE",
        })
        assert dispatcher._queue.qsize() == 1

    def test_queue_overflow_drops_gracefully(self):
        """Test that queue overflow doesn't crash."""
        dispatcher = self._make_dispatcher()
        dispatcher._queue = asyncio.Queue(maxsize=2)
        dispatcher.send("scan_started", {"target_url": "t1"})
        dispatcher.send("scan_started", {"target_url": "t2"})
        dispatcher.send("scan_started", {"target_url": "t3"})  # should be dropped
        assert dispatcher._queue.qsize() == 2

    @pytest.mark.asyncio
    async def test_start_noop_when_disabled(self):
        """Test that start() is a no-op when notifications are disabled."""
        dispatcher = self._make_dispatcher(enabled=False)
        await dispatcher.start()
        assert dispatcher._worker_task is None
        assert dispatcher._running is False

    @pytest.mark.asyncio
    async def test_close_graceful(self):
        """Test that close() shuts down cleanly."""
        dispatcher = self._make_dispatcher()
        await dispatcher.close()  # should not raise even if never started

    @pytest.mark.asyncio
    async def test_deliver_handles_offline_gateway(self):
        """Test that delivery doesn't crash when gateway is offline."""
        dispatcher = self._make_dispatcher()
        item = {
            "event_type": "scan_started",
            "data": {"target_url": "https://example.com"},
            "attempts": 2,  # Already at max-1 retries
            "queued_at": 0,
        }
        # Mock _ensure_connection to return None (gateway offline)
        dispatcher._ensure_connection = AsyncMock(return_value=None)
        await dispatcher._deliver(item)
        # Should have been requeued (attempt 3 → dropped)
        assert dispatcher._queue.qsize() == 0  # dropped after max retries

    @pytest.mark.asyncio
    async def test_deliver_sends_frame(self):
        """Test that delivery sends a properly formatted frame."""
        dispatcher = self._make_dispatcher()
        mock_ws = AsyncMock()
        dispatcher._ensure_connection = AsyncMock(return_value=mock_ws)

        item = {
            "event_type": "scan_started",
            "data": {"target_url": "https://example.com"},
            "attempts": 0,
            "queued_at": 0,
        }
        await dispatcher._deliver(item)

        mock_ws.send.assert_called_once()
        frame = json.loads(mock_ws.send.call_args[0][0])
        assert frame["type"] == "event.signal"
        assert frame["name"] == "NOTIFICATION"
        assert frame["payload"]["event"] == "scan_started"
        assert "🎯" in frame["payload"]["title"]
