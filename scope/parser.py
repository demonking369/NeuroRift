#!/usr/bin/env python3
"""NeuroRift v2 — Scope parser. Normalizes all scope formats into ScopeMap."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ScopeEntry:
    raw: str
    is_wildcard: bool = False
    is_ip_range: bool = False
    ports: Optional[List[int]] = None


@dataclass
class ScopeMap:
    in_scope: List[ScopeEntry] = field(default_factory=list)
    out_of_scope: List[ScopeEntry] = field(default_factory=list)

    def __str__(self) -> str:
        in_strs = [e.raw for e in self.in_scope]
        out_strs = [e.raw for e in self.out_of_scope]
        return f"IN-SCOPE: {', '.join(in_strs)} | OUT-OF-SCOPE: {', '.join(out_strs)}"


def _parse_entry(raw: str) -> ScopeEntry:
    raw = raw.strip()
    is_wildcard = raw.startswith("*.")
    is_ip_range = "/" in raw and any(c.isdigit() for c in raw.split("/")[0].split(".")[-1])
    return ScopeEntry(raw=raw, is_wildcard=is_wildcard, is_ip_range=is_ip_range)


def parse_scope(source: str) -> ScopeMap:
    """
    Parse scope from multiple formats:
    - Plain domain list (one per line)
    - HackerOne markdown table (| Asset | Type | Scope |)
    - Bugcrowd JSON ({"targets": {"in_scope": [...], "out_of_scope": [...]}})
    - Wildcard domains (*.example.com)
    - IP ranges in CIDR notation
    """
    scope_map = ScopeMap()

    # Try Bugcrowd JSON
    try:
        data = json.loads(source)
        for entry in data.get("targets", {}).get("in_scope", []):
            target = entry.get("target") or entry.get("asset") or str(entry)
            scope_map.in_scope.append(_parse_entry(target))
        for entry in data.get("targets", {}).get("out_of_scope", []):
            target = entry.get("target") or entry.get("asset") or str(entry)
            scope_map.out_of_scope.append(_parse_entry(target))
        return scope_map
    except (json.JSONDecodeError, AttributeError):
        pass

    # Try HackerOne markdown table
    if "|" in source:
        in_scope_section = True
        for line in source.splitlines():
            line = line.strip()
            if not line.startswith("|") or "---" in line:
                if "out of scope" in line.lower():
                    in_scope_section = False
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 1 and cols[0] and not cols[0].lower().startswith("asset"):
                entry = _parse_entry(cols[0])
                if in_scope_section:
                    scope_map.in_scope.append(entry)
                else:
                    scope_map.out_of_scope.append(entry)
        if scope_map.in_scope:
            return scope_map

    # Plain domain/IP list — one per line
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        scope_map.in_scope.append(_parse_entry(line))

    return scope_map


def parse_scope_file(path: str) -> ScopeMap:
    """Load scope from a file path."""
    return parse_scope(Path(path).read_text(encoding="utf-8"))
