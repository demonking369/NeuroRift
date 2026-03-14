"""Package-level CLI helper that delegates to global entrypoint."""
from __future__ import annotations

from neurorift_cli import build_parser, install_global_wrapper, main

__all__ = ["build_parser", "install_global_wrapper", "main"]
