"""Global NeuroRift CLI entrypoint with optional /usr/local/bin wrapper installer."""
from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from pathlib import Path

import neurorift_main


def install_global_wrapper() -> int:
    wrapper_path = Path("/usr/local/bin/neurorift")
    main_path = (Path(__file__).resolve().parent / "neurorift_main.py").resolve()
    script = f"#!/usr/bin/env bash\npython3 {main_path} \"$@\"\n"
    try:
        wrapper_path.write_text(script, encoding="utf-8")
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except PermissionError:
        print("Permission denied writing /usr/local/bin/neurorift. Re-run with sudo.")
        return 1
    except Exception as exc:
        print(f"Failed to install wrapper: {exc}")
        return 1

    print(f"Installed global wrapper at {wrapper_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NeuroRift global CLI launcher")
    parser.add_argument("--install-global-wrapper", action="store_true", help="Install /usr/local/bin/neurorift wrapper")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments forwarded to neurorift_main.py")
    return parser


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()

    if ns.install_global_wrapper:
        return install_global_wrapper()

    forwarded = ns.args or []
    if forwarded and forwarded[0] == "--":
        forwarded = forwarded[1:]

    # Route into existing app entrypoint; keep compatibility with current parser.
    sys.argv = ["neurorift"] + forwarded
    neurorift_main.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
