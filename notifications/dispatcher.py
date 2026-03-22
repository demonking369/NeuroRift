#!/usr/bin/env python3
"""Async notification dispatcher for NeuroRift.

Connects to the OpenClaw Gateway WebSocket and sends real-time
scan event notifications to user-configured messaging channels.

Key guarantees:
- Notification failure NEVER crashes or pauses the scan
- Gateway connection is async — never blocks the pipeline
- Failed notifications are queued and retried (max 3 attempts)
- Credentials are never logged
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

from notifications.config_loader import NotificationConfig, load_config
from notifications.templates import render

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5  # seconds — exponential backoff
QUEUE_MAX_SIZE = 100
RECONNECT_DELAY_BASE = 2.0
RECONNECT_MAX_DELAY = 60.0


class NotificationDispatcher:
    """Async dispatcher that sends notification events through OpenClaw Gateway.

    Usage:
        dispatcher = NotificationDispatcher()
        await dispatcher.start()
        dispatcher.send("scan_started", {"target_url": "https://example.com"})
        ...
        await dispatcher.close()
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config: NotificationConfig = load_config(config_path)
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
        self._ws: Any = None
        self._worker_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._session_id = f"nr-notify-{uuid.uuid4().hex[:8]}"

    async def start(self) -> None:
        """Start the background notification worker.

        Safe to call even if notifications are disabled — it becomes a no-op.
        """
        if not self.config.enabled:
            logger.info("Notifications disabled — dispatcher idle")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info(
            "Notification dispatcher started (gateway=%s, channels=%s)",
            self.config.gateway_url,
            self.config.get_active_channels(),
        )

    async def close(self) -> None:
        """Gracefully shut down the dispatcher."""
        self._running = False

        if self._worker_task and not self._worker_task.done():
            # Drain remaining items with a short timeout
            try:
                await asyncio.wait_for(self._drain_queue(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Notification queue drain timed out — dropping remaining")

            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        logger.info("Notification dispatcher stopped")

    def send(self, event_type: str, data: Dict[str, Any]) -> None:
        """Queue a notification event for async delivery.

        This method is synchronous and non-blocking — it just puts
        the event into the async queue. Safe to call from anywhere
        in the pipeline.

        Args:
            event_type: Event type key (e.g. 'scan_started', 'vulnerability_found')
            data: Dict of template variables for this event type
        """
        if not self.config.enabled:
            return

        severity = data.get("severity")
        if not self.config.should_notify(event_type, severity):
            return

        try:
            self._queue.put_nowait({
                "event_type": event_type,
                "data": data,
                "attempts": 0,
                "queued_at": time.time(),
            })
        except asyncio.QueueFull:
            logger.warning("Notification queue full — dropping %s event", event_type)

    # ─── Internal ────────────────────────────────────────────────

    async def _worker_loop(self) -> None:
        """Background worker that drains the queue and sends to gateway."""
        while self._running:
            try:
                item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            await self._deliver(item)

    async def _deliver(self, item: Dict[str, Any]) -> None:
        """Attempt to deliver a single notification with retry."""
        event_type = item["event_type"]
        data = item["data"]
        attempts = item["attempts"]

        msg = render(event_type, data)
        frame = {
            "type": "event.signal",
            "name": "NOTIFICATION",
            "session": {"id": self._session_id, "mode": "isolated"},
            "payload": {
                "event": event_type,
                "title": msg.title,
                "body": msg.body,
                "severity": msg.severity,
                "channels": self.config.get_active_channels(),
            },
            "ts": int(time.time() * 1000),
        }

        try:
            ws = await self._ensure_connection()
            if ws is None:
                # Gateway offline — requeue with backoff
                await self._requeue(item)
                return

            await ws.send(json.dumps(frame))
            logger.debug("Sent %s notification", event_type)
        except Exception as exc:
            logger.warning("Notification delivery failed (%s): %s", event_type, exc)
            await self._requeue(item)

    async def _requeue(self, item: Dict[str, Any]) -> None:
        """Requeue a failed notification with exponential backoff."""
        item["attempts"] += 1
        if item["attempts"] >= MAX_RETRIES:
            logger.warning(
                "Notification %s dropped after %d attempts",
                item["event_type"],
                MAX_RETRIES,
            )
            return

        backoff = RETRY_BACKOFF_BASE ** item["attempts"]
        await asyncio.sleep(backoff)

        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            logger.warning("Notification queue full on requeue — dropping %s", item["event_type"])

    async def _ensure_connection(self) -> Any:
        """Ensure WebSocket connection to gateway, reconnecting if needed."""
        if self._ws is not None:
            try:
                # Check if connection is still alive
                await self._ws.ping()
                return self._ws
            except Exception:
                self._ws = None

        try:
            import websockets
            self._ws = await asyncio.wait_for(
                websockets.connect(
                    self.config.gateway_url,
                    ping_interval=20,
                    ping_timeout=10,
                ),
                timeout=5.0,
            )
            logger.info("Connected to OpenClaw Gateway at %s", self.config.gateway_url)
            return self._ws
        except Exception as exc:
            logger.debug("Gateway connection failed: %s", exc)
            self._ws = None
            return None

    async def _drain_queue(self) -> None:
        """Drain remaining items in the queue."""
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                await self._deliver(item)
            except asyncio.QueueEmpty:
                break
