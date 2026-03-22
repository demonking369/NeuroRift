#!/usr/bin/env python3
"""NeuroRift v2 — network_bridge.py: Python wrapper for C network binaries."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)
BINARY_DIR = Path(__file__).parent


class NetworkBridgeError(Exception):
    pass


class NetworkBridge:
    def _run(self, binary: str, args: list) -> Dict[str, Any]:
        b = BINARY_DIR / binary
        if not b.exists():
            raise NetworkBridgeError(f"{binary} not built. Run: make -C network/")
        result = subprocess.run(
            [str(b)] + args, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise NetworkBridgeError(f"{binary} failed: {result.stderr.strip()[:300]}")
        return json.loads(result.stdout.strip())

    def tcp_probe(self, host: str, port: int, timeout_ms: int = 2000) -> Dict[str, Any]:
        return self._run(
            "tcp_probe",
            ["--target", host, "--port", str(port), "--timeout", str(timeout_ms)],
        )

    def packet_crafter(
        self, src_ip: str, dst_ip: str, dst_port: int, ttl: int = 64
    ) -> Dict[str, Any]:
        return self._run(
            "packet_crafter",
            [
                "--src-ip",
                src_ip,
                "--dst-ip",
                dst_ip,
                "--dst-port",
                str(dst_port),
                "--ttl",
                str(ttl),
            ],
        )

    def check_raw_socket(self) -> Dict[str, Any]:
        return self._run("raw_socket", [])
