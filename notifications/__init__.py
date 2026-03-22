#!/usr/bin/env python3
"""NeuroRift Notification System — OpenClaw Gateway Integration.

Sends real-time scan updates to user's preferred messaging platforms
via the OpenClaw Gateway WebSocket.
"""

from notifications.dispatcher import NotificationDispatcher

__all__ = ["NotificationDispatcher"]
