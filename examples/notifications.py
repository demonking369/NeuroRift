#!/usr/bin/env python3
"""
Example usage of the NeuroRift notification system
"""

import asyncio
import logging
from pathlib import Path
from utils.notifier import Notifier
from utils.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Initialize config manager
    config_path = Path.home() / ".neurorift" / "config.json"
    config = ConfigManager(config_path)

    # Initialize notifier
    notifier = Notifier(config)
    await notifier.start()

    try:
        # Example 1: Basic notification
        await notifier.notify("Scan started for example.com", "info")

        # Example 2: Vulnerability found
        await notifier.notify(
            "SQL Injection vulnerability detected",
            "high",
            data={
                "vulnerability": "SQL Injection",
                "affected_url": "https://example.com/login",
                "payload": "' OR '1'='1",
                "confidence": "high",
            },
        )

        # Example 3: Critical finding
        await notifier.notify(
            "Remote Code Execution vulnerability found!",
            "critical",
            data={
                "vulnerability": "RCE",
                "affected_component": "File Upload Handler",
                "cve": "CVE-2023-1234",
                "exploit_available": True,
            },
            channels=["email", "discord"],  # Send to specific channels
        )

        # Example 4: Scan completion
        await notifier.notify(
            "Scan completed successfully",
            "info",
            data={
                "target": "example.com",
                "duration": "2h 15m",
                "findings": {"critical": 1, "high": 3, "medium": 5, "low": 8},
            },
        )

        # Wait for notifications to be processed
        await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error in notification example: {e}")
    finally:
        await notifier.stop()


if __name__ == "__main__":
    asyncio.run(main())
