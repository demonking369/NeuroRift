#!/usr/bin/env python3
"""Preflight checks for NeuroRift × OpenClaw runtime stability."""

from __future__ import annotations

import os
import socket
import sys
from typing import Iterable

REQUIRED_ENV = [
    "OPENCLAW_CONFIG_PATH",
    "OPENCLAW_STATE_DIR",
    "LLAMA_HOST",
    "NEURORIFT_BRIDGE_URL",
]

PORTS = [18789, 8766, 8765, 3000, 8080]


def _check_env(keys: Iterable[str]) -> list[str]:
    missing = []
    for key in keys:
        value = os.getenv(key, "").strip()
        if not value:
            missing.append(key)
    return missing


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    missing = _check_env(REQUIRED_ENV)
    if missing:
        print(f"[FAIL] Missing required env vars: {', '.join(missing)}")
        return 1

    print("[OK] Required env vars present")

    collisions = [port for port in PORTS if _port_in_use(port)]
    if collisions:
        print(f"[WARN] Ports currently in use: {', '.join(map(str, collisions))}")
    else:
        print("[OK] No expected runtime ports in use")

    print("[OK] Doctor completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
