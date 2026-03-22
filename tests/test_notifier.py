#!/usr/bin/env python3
"""
Test suite for the notification system
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest_asyncio
from utils.notifier import Notifier


@pytest_asyncio.fixture
async def notifier():
    """Create a test notifier instance"""
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)

    config = {
        "notifications": {
            "enabled": True,
            "email": {
                "enabled": True,
                "smtp_server": "smtp.test.com",
                "smtp_port": 587,
                "username": "test@test.com",
                "password": "test123",
            },
            "discord": {
                "enabled": True,
                "webhook_url": "https://discord.com/api/webhooks/test",
            },
            "webhook": {"enabled": True, "url": "https://webhook.test.com"},
        }
    }

    config_path = test_dir / "test_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    notifier = Notifier(str(test_dir), str(config_path))
    yield notifier

    # Cleanup
    if test_dir.exists():
        for file in test_dir.glob("*"):
            file.unlink()
        test_dir.rmdir()


@pytest.mark.asyncio
async def test_notify_basic(notifier):
    """Test basic notification"""
    with patch("utils.notifier.Notifier._process_notification") as mock_process:
        await notifier.notify("Test message", "info")
        mock_process.assert_called_once_with("Test message", "info", None, [])


@pytest.mark.asyncio
async def test_notify_with_data(notifier):
    """Test notification with additional data"""
    test_data = {
        "vulnerability": "SQL Injection",
        "severity": "high",
        "affected_url": "https://example.com/login",
    }

    with patch("utils.notifier.Notifier._process_notification") as mock_process:
        await notifier.notify("Vulnerability found", "high", data=test_data)
        mock_process.assert_called_once_with(
            "Vulnerability found", "high", test_data, []
        )


@pytest.mark.asyncio
async def test_notify_specific_channels(notifier):
    """Test notification to specific channels"""
    with patch("utils.notifier.Notifier._process_notification") as mock_process:
        await notifier.notify("Test message", "info", channels=["email", "discord"])
        mock_process.assert_called_once_with(
            "Test message", "info", None, ["email", "discord"]
        )


@pytest.mark.asyncio
async def test_email_notification(notifier):
    """Test email notification sending"""
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__.return_value = mock_smtp.return_value

        await notifier.notify("Test email", "critical", channels=["email"])

        mock_smtp.assert_called_once_with("smtp.test.com", 587)
        mock_smtp.return_value.starttls.assert_called_once()
        mock_smtp.return_value.login.assert_called_once_with("test@test.com", "test123")
        mock_smtp.return_value.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_discord_notification(notifier):
    """Test Discord notification sending"""
    mock_response = AsyncMock()
    mock_response.text = AsyncMock(return_value="")
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    with patch("aiohttp.ClientSession", return_value=mock_cm):
        await notifier.notify(
            "Test Discord",
            "high",
            data={"finding": "XSS vulnerability"},
            channels=["discord"],
        )

        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://discord.com/api/webhooks/test"
        assert "embeds" in call_args[1]["json"]


@pytest.mark.asyncio
async def test_webhook_notification(notifier):
    """Test generic webhook notification"""
    mock_response = AsyncMock()
    mock_response.text = AsyncMock(return_value="")
    mock_session = AsyncMock()
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_session
    mock_cm.__aexit__.return_value = None

    with patch("aiohttp.ClientSession", return_value=mock_cm):
        test_data = {
            "scan_id": "123",
            "target": "example.com",
            "findings": ["vuln1", "vuln2"],
        }

        await notifier.notify(
            "Test webhook", "medium", data=test_data, channels=["webhook"]
        )

        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://webhook.test.com"
        assert call_args[1]["json"]["message"] == "Test webhook"
        assert call_args[1]["json"]["severity"] == "medium"
        assert call_args[1]["json"]["data"] == test_data


@pytest.mark.asyncio
async def test_severity_colors(notifier):
    """Test severity color mapping"""
    colors = {
        "critical": 0xFF0000,
        "high": 0xFFA500,
        "medium": 0xFFFF00,
        "low": 0x00FF00,
        "info": 0x0000FF,
    }

    for severity, expected_color in colors.items():
        color = notifier._get_severity_color(severity)
        assert color == expected_color, f"Wrong color for {severity}"
