#!/usr/bin/env python3
"""
NeuroRift Auto-Save Service
Background service for automatic session persistence.

Designed and developed by demonking369
"""

import threading
import time
import logging
import signal
import atexit
from typing import Optional, Callable
from datetime import datetime


class AutoSaveService:
    """
    Background service that automatically saves sessions.

    Features:
    - Periodic auto-save (configurable interval)
    - Event-driven saves
    - Graceful shutdown handling
    - Crash recovery
    """

    def __init__(
        self,
        session_manager,
        interval_seconds: int = 300,  # 5 minutes default
        enabled: bool = True,
    ):
        """
        Initialize auto-save service.

        Args:
            session_manager: SessionManager instance
            interval_seconds: Auto-save interval in seconds
            enabled: Enable auto-save on initialization
        """
        self.session_manager = session_manager
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)

        # Threading
        self._stop_event = threading.Event()
        self._save_thread: Optional[threading.Thread] = None
        self._last_save_time: Optional[datetime] = None

        # Event callbacks
        self._on_save_callbacks: list[Callable] = []

        # Register shutdown handlers
        try:
            self._register_shutdown_handlers()
        except ValueError:
            self.logger.warning(
                "Could not register signal handlers (not in main thread). Auto-save on exit relies on atexit."
            )

        if self.enabled:
            self.start()

    def _register_shutdown_handlers(self):
        """Register handlers for graceful shutdown"""
        # Handle Ctrl+C (only works in main thread)
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            else:
                self.logger.debug("Skipping signal registration (not key thread)")
        except ValueError:
            self.logger.debug("Skipping signal registration (interpreter constraint)")

        # Handle normal exit - safe in any thread context if supported
        atexit.register(self._on_exit)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, saving session...")
        self.save_now()
        self.stop()

    def _on_exit(self):
        """Handle normal exit"""
        self.logger.info("Application exiting, saving session...")
        self.save_now()
        self.stop()

    def start(self):
        """Start auto-save service"""
        if self._save_thread and self._save_thread.is_alive():
            self.logger.warning("Auto-save service already running")
            return

        self._stop_event.clear()
        self._save_thread = threading.Thread(
            target=self._auto_save_loop, daemon=True, name="AutoSaveThread"
        )
        self._save_thread.start()

        self.logger.info(
            f"Auto-save service started (interval: {self.interval_seconds}s)"
        )

    def stop(self):
        """Stop auto-save service"""
        if not self._save_thread or not self._save_thread.is_alive():
            return

        self._stop_event.set()
        self._save_thread.join(timeout=5)

        self.logger.info("Auto-save service stopped")

    def _auto_save_loop(self):
        """Main auto-save loop"""
        while not self._stop_event.is_set():
            try:
                # Wait for interval or stop event
                if self._stop_event.wait(timeout=self.interval_seconds):
                    break

                # Perform auto-save
                self._perform_auto_save()

            except Exception as e:
                self.logger.error(f"Auto-save error: {e}", exc_info=True)

    def _perform_auto_save(self):
        """Perform automatic save"""
        try:
            # Check if there's an active session
            if not self.session_manager.current_session_id:
                self.logger.debug("No active session to auto-save")
                return

            # Save session
            self.session_manager.save_session()
            self._last_save_time = datetime.now()

            # Trigger callbacks
            for callback in self._on_save_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Save callback error: {e}")

            self.logger.debug(
                f"Auto-saved session: {self.session_manager.current_session_id}"
            )

        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}", exc_info=True)

    def save_now(self):
        """Trigger immediate save"""
        self.logger.info("Immediate save triggered")
        self._perform_auto_save()

    def on_save(self, callback: Callable):
        """
        Register callback to be called after each save.

        Args:
            callback: Function to call after save
        """
        self._on_save_callbacks.append(callback)

    def get_last_save_time(self) -> Optional[datetime]:
        """Get timestamp of last save"""
        return self._last_save_time

    def set_interval(self, interval_seconds: int):
        """
        Change auto-save interval.

        Args:
            interval_seconds: New interval in seconds
        """
        self.interval_seconds = interval_seconds
        self.logger.info(f"Auto-save interval changed to {interval_seconds}s")

    def enable(self):
        """Enable auto-save"""
        if not self.enabled:
            self.enabled = True
            self.start()
            self.logger.info("Auto-save enabled")

    def disable(self):
        """Disable auto-save"""
        if self.enabled:
            self.enabled = False
            self.stop()
            self.logger.info("Auto-save disabled")


class EventDrivenSave:
    """
    Triggers saves based on specific events.

    Events:
    - Task completion
    - Mode change
    - Tool execution
    - Error occurrence
    """

    def __init__(self, auto_save_service: AutoSaveService):
        self.auto_save_service = auto_save_service
        self.logger = logging.getLogger(__name__)

    def on_task_complete(self):
        """Trigger save on task completion"""
        self.logger.info("Task completed, saving session...")
        self.auto_save_service.save_now()

    def on_mode_change(self, old_mode: str, new_mode: str):
        """Trigger save on mode change"""
        self.logger.info(f"Mode changed: {old_mode} → {new_mode}, saving session...")
        self.auto_save_service.save_now()

    def on_tool_execution(self, tool_name: str):
        """Trigger save after tool execution"""
        self.logger.debug(f"Tool executed: {tool_name}, saving session...")
        self.auto_save_service.save_now()

    def on_error(self, error: Exception):
        """Trigger save on error (for recovery)"""
        self.logger.error(f"Error occurred: {error}, saving session for recovery...")
        self.auto_save_service.save_now()

    def on_checkpoint(self):
        """Trigger save for checkpoint"""
        self.logger.info("Creating checkpoint...")
        self.auto_save_service.save_now()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from modules.session import SessionManager

    # Initialize session manager
    session_manager = SessionManager()

    # Create a session
    session_id = session_manager.create_session(name="Test Auto-Save", mode="offensive")

    # Initialize auto-save service
    auto_save = AutoSaveService(
        session_manager, interval_seconds=10, enabled=True  # 10 seconds for testing
    )

    # Register callback
    def on_save_callback():
        print("Session saved!")

    auto_save.on_save(on_save_callback)

    # Initialize event-driven saves
    event_save = EventDrivenSave(auto_save)

    print("Auto-save service running...")
    print("Press Ctrl+C to exit")

    try:
        # Simulate some work
        time.sleep(30)

        # Trigger event-driven save
        event_save.on_task_complete()

        time.sleep(10)

    except KeyboardInterrupt:
        print("\nShutting down...")

    auto_save.stop()
