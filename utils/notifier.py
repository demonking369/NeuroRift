#!/usr/bin/env python3
"""
Notification system for NeuroRift
"""

import json
import logging
import smtplib
import aiohttp
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class Notifier:
    """Handles notifications for various channels"""

    def __init__(self, base_dir: str, config_path: str):
        """Initialize notifier with configuration"""
        self.base_dir = Path(base_dir)
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load notification configuration"""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {"notifications": {"enabled": False}}

    async def notify(
        self,
        message: str,
        severity: str = "info",
        data: Optional[Dict] = None,
        channels: Optional[List[str]] = None,
    ) -> None:
        """Send notification to specified channels"""
        if not self.config["notifications"]["enabled"]:
            return

        if channels is None:
            channels = []

        await self._process_notification(message, severity, data, channels)

    async def _process_notification(
        self, message: str, severity: str, data: Optional[Dict], channels: List[str]
    ) -> None:
        """Process notification for each channel"""
        tasks = []

        if "email" in channels and self.config["notifications"]["email"]["enabled"]:
            tasks.append(self._send_email(message, severity, data))

        if "discord" in channels and self.config["notifications"]["discord"]["enabled"]:
            tasks.append(self._send_discord(message, severity, data))

        if "webhook" in channels and self.config["notifications"]["webhook"]["enabled"]:
            tasks.append(self._send_webhook(message, severity, data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_email(
        self, message: str, severity: str, data: Optional[Dict]
    ) -> None:
        """Send email notification"""
        try:
            email_config = self.config["notifications"]["email"]
            msg = MIMEMultipart()
            msg["From"] = email_config["username"]
            msg["To"] = email_config["username"]
            msg["Subject"] = f"NeuroRift Alert: {severity.upper()}"

            body = f"Message: {message}\nSeverity: {severity}\n"
            if data:
                body += f"\nAdditional Data:\n{json.dumps(data, indent=2)}"

            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(
                email_config["smtp_server"], email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")

    async def _send_discord(
        self, message: str, severity: str, data: Optional[Dict]
    ) -> None:
        """Send Discord notification"""
        try:
            webhook_url = self.config["notifications"]["discord"]["webhook_url"]
            color = self._get_severity_color(severity)

            embed = {
                "title": f"NeuroRift Alert: {severity.upper()}",
                "description": message,
                "color": color,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),  # Changed datetime.utcnow() to datetime.now(UTC)
            }

            if data:
                embed["fields"] = [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in data.items()
                ]

            async with aiohttp.ClientSession() as session:
                response = await session.post(webhook_url, json={"embeds": [embed]})
                await response.text()

        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {e}")

    async def _send_webhook(
        self, message: str, severity: str, data: Optional[Dict]
    ) -> None:
        """Send generic webhook notification"""
        try:
            webhook_url = self.config["notifications"]["webhook"]["url"]
            payload = {
                "message": message,
                "severity": severity,
                "timestamp": datetime.now(
                    timezone.utc
                ).isoformat(),  # Changed datetime.utcnow() to datetime.now(UTC)
            }

            if data:
                payload["data"] = data

            async with aiohttp.ClientSession() as session:
                response = await session.post(webhook_url, json=payload)
                await response.text()

        except Exception as e:
            self.logger.error(f"Failed to send webhook notification: {e}")

    def _get_severity_color(self, severity: str) -> int:
        """Get color code for severity level"""
        colors = {
            "critical": 0xFF0000,  # Red
            "high": 0xFFA500,  # Orange
            "medium": 0xFFFF00,  # Yellow
            "low": 0x00FF00,  # Green
            "info": 0x0000FF,  # Blue
        }
        return colors.get(severity.lower(), 0x808080)  # Default to gray
