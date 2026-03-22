"""
Stealth utilities for NeuroRift
"""

import random
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging


class StealthManager:
    def __init__(self):
        self.min_delay = 1.0
        self.max_delay = 3.0
        self.proxies: List[str] = []
        self.current_proxy: Optional[str] = None
        self.request_count = 0
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)

    def set_delay_range(self, min_delay: float, max_delay: float):
        """Set delay range for requests"""
        self.min_delay = min_delay
        self.max_delay = max_delay

    def load_proxies_from_file(self, proxy_file: str):
        """Load proxies from file"""
        try:
            with open(proxy_file) as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            self.logger.info(f"Loaded {len(self.proxies)} proxies")
        except Exception as e:
            self.logger.error(f"Error loading proxies: {e}")

    def get_random_proxy(self) -> Optional[str]:
        """Get random proxy from list"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def rotate_proxy(self):
        """Rotate to next proxy"""
        if not self.proxies:
            return

        if self.current_proxy in self.proxies:
            current_index = self.proxies.index(self.current_proxy)
            next_index = (current_index + 1) % len(self.proxies)
        else:
            next_index = 0

        self.current_proxy = self.proxies[next_index]
        self.logger.debug(f"Rotated to proxy: {self.current_proxy}")

    def get_request_delay(self) -> float:
        """Get random delay for request"""
        return random.uniform(self.min_delay, self.max_delay)

    def wait_before_request(self):
        """Wait before making request"""
        delay = self.get_request_delay()
        time.sleep(delay)
        self.last_request_time = time.time()
        self.request_count += 1

    def get_request_stats(self) -> Dict:
        """Get request statistics"""
        return {
            "total_requests": self.request_count,
            "total_proxies": len(self.proxies),
            "min_delay": self.min_delay,
            "max_delay": self.max_delay,
            "last_request": (
                time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(self.last_request_time)
                )
                if self.last_request_time
                else "Never"
            ),
        }


# Global stealth manager instance
stealth_manager = StealthManager()
