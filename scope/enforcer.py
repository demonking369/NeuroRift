#!/usr/bin/env python3
"""
NeuroRift v2 — Scope enforcer.
Hard constraint layer that runs before EVERY tool call.
This is the legal protection layer — never bypass.
"""

import functools
import fnmatch
import logging
import re
from typing import Any, Callable
from urllib.parse import urlparse, unquote

from scope.parser import ScopeMap, ScopeEntry

logger = logging.getLogger(__name__)


class OutOfScopeError(Exception):
    """Raised when a target is outside the defined scope."""


def _normalize_target(target: str) -> str:
    """Extract hostname/IP from URL or bare host string."""
    if target.startswith(("http://", "https://")):
        parsed = urlparse(target)
        host = parsed.hostname or ""
    else:
        # Strip port
        host = re.split(r":\d+", target)[0]
    # URL-decode to catch bypass attempts like %00, %2e
    return unquote(host).lower()


def _matches_entry(host: str, entry: ScopeEntry) -> bool:
    """Check if normalized host matches a scope entry."""
    pattern = entry.raw.lower()

    if entry.is_wildcard:
        # *.example.com matches sub.example.com but NOT example.com itself
        base = pattern.lstrip("*.")
        return host == base or host.endswith("." + base)

    if entry.is_ip_range:
        # Simple CIDR check
        try:
            import ipaddress

            return ipaddress.ip_address(host) in ipaddress.ip_network(
                pattern, strict=False
            )
        except ValueError:
            pass

    return host == pattern or fnmatch.fnmatch(host, pattern)


def is_in_scope(target: str, scope_map: ScopeMap) -> bool:
    """Return True if target is in scope and not explicitly out-of-scope."""
    host = _normalize_target(target)

    # First check explicit out-of-scope (takes priority)
    for entry in scope_map.out_of_scope:
        if _matches_entry(host, entry):
            return False

    # Then check in-scope
    for entry in scope_map.in_scope:
        if _matches_entry(host, entry):
            return True

    return False


def enforce_scope(scope_map: ScopeMap):
    """
    Decorator factory. Wraps a tool function to enforce scope before execution.

    Usage:
        @enforce_scope(scope_map)
        def run_sqli(target: str, **kwargs):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            # 'target' is always the first positional arg or a keyword arg
            target = args[0] if args else kwargs.get("target", "")
            if not is_in_scope(str(target), scope_map):
                logger.warning("SCOPE VIOLATION BLOCKED: %s → %s", fn.__name__, target)
                raise OutOfScopeError(
                    f"Target '{target}' is OUT OF SCOPE. Tool '{fn.__name__}' call was blocked."
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
