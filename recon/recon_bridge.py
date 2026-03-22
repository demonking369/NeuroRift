#!/usr/bin/env python3
"""NeuroRift v2 — recon_bridge.py: Python subprocess wrapper for the Rust recon binary."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

BINARY = Path(__file__).parent / "target" / "release" / "recon"


class ReconBridgeError(Exception):
    pass


class ReconBridge:
    """
    Wraps the compiled Rust recon binary.
    All output from the binary is JSON on stdout. Errors go to stderr.
    """

    def __init__(self, binary_path: Optional[str] = None, default_timeout: int = 120):
        self.binary = Path(binary_path) if binary_path else BINARY
        self.default_timeout = default_timeout

        if not self.binary.exists():
            raise ReconBridgeError(
                f"Recon binary not found at {self.binary}. Run 'cargo build --release' in recon/"
            )

    def run(self, mode: str, target: str, **kwargs) -> Dict[str, Any]:
        """
        Run the recon binary in the given mode.

        Args:
            mode: One of subdomain, port, fuzz, dns, probe
            target: Domain, IP, or URL
            **kwargs: Additional CLI flags (wordlist, concurrency, timeout, ports)

        Returns:
            Parsed JSON dict from binary stdout

        Raises:
            ReconBridgeError: if binary missing, non-zero exit code, or malformed JSON
        """
        if not self.binary.exists():
            raise ReconBridgeError(
                f"Recon binary not built. Run: cd recon && cargo build --release"
            )

        cmd = [str(self.binary), "--mode", mode, "--target", target]

        for key, value in kwargs.items():
            flag = f"--{key.replace('_', '-')}"
            cmd.extend([flag, str(value)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.default_timeout,
            )
        except subprocess.TimeoutExpired:
            raise ReconBridgeError(
                f"Recon timeout exceeded after {self.default_timeout}s"
            )

        if result.returncode != 0:
            raise ReconBridgeError(
                f"Recon binary exited {result.returncode}: {result.stderr.strip()[:500]}"
            )

        if not result.stdout.strip():
            raise ReconBridgeError("Recon binary produced no output")

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise ReconBridgeError(
                f"Recon binary output is not valid JSON: {e}\n{result.stdout[:300]}"
            )

    def subdomain_enum(
        self, target: str, wordlist: str = "", concurrency: int = 1000
    ) -> Dict[str, Any]:
        return self.run("subdomain", target, wordlist=wordlist, concurrency=concurrency)

    def port_scan(
        self, target: str, ports: str = "1-1024", concurrency: int = 500
    ) -> Dict[str, Any]:
        return self.run("port", target, ports=ports, concurrency=concurrency)

    def fuzz_endpoints(
        self, target: str, wordlist: str = "", concurrency: int = 200
    ) -> Dict[str, Any]:
        return self.run("fuzz", target, wordlist=wordlist, concurrency=concurrency)

    def dns_resolve(self, target: str) -> Dict[str, Any]:
        return self.run("dns", target)

    def http_probe(self, target: str) -> Dict[str, Any]:
        return self.run("probe", target)
