#!/usr/bin/env python3
"""
NeuroRift v2 — main.py
Multi-language AI-driven security assessment pipeline.

Usage: python main.py --scope scope.txt --target https://example.com
"""

import argparse
import asyncio
import logging
import sys
import uuid
import yaml
from pathlib import Path

# Configure logging before any imports that use it
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("neurorift")


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_tool_registry(scope_map, config: dict):
    """Register all AI-callable tools with scope enforcer applied."""
    from scope.enforcer import enforce_scope
    from tools.sqli import SQLiTool
    from tools.xss import XSSTool
    from tools.idor import IDORTool
    from tools.ssrf import SSRFTool
    from tools.ssti import SSTITool
    from tools.xxe import XXETool
    from tools.open_redirect import OpenRedirectTool
    from tools.auth_bypass import AuthBypassTool
    from tools.race_condition import RaceConditionTool
    from tools.shell_exec import ShellExecTool

    registry = {}
    for tool_class in [
        SQLiTool,
        XSSTool,
        IDORTool,
        SSRFTool,
        SSTITool,
        XXETool,
        OpenRedirectTool,
        AuthBypassTool,
        RaceConditionTool,
        ShellExecTool,
    ]:
        instance = tool_class()
        enforced = enforce_scope(scope_map)(instance.run)
        registry[instance.name] = enforced

    return registry


async def run_assessment(args: argparse.Namespace, config: dict) -> None:
    from ai.llama_client import LlamaClient, LlamaServerError
    from scope.parser import parse_scope_file
    from session.state import SessionState
    from session.compressor import Compressor
    from reporting.reporter import Reporter
    from ai.planner import Planner
    from ai.executor import Executor
    from recon.recon_bridge import ReconBridge

    # 1. Check llama.cpp health — fail fast, never hang
    llama_cfg = config.get("llama", {})
    client = LlamaClient(
        base_url=llama_cfg.get("base_url", "http://localhost:8080/v1"),
        timeout=llama_cfg.get("timeout_seconds", 300),
    )
    try:
        client.check_health()
        logger.info("✅ llama.cpp server healthy")
    except LlamaServerError as e:
        logger.error("❌ llama.cpp unavailable: %s", e)
        sys.exit(1)

    # 2. Parse scope
    scope_map = parse_scope_file(args.scope)
    logger.info(
        "📋 Scope loaded: %d in-scope, %d out-of-scope entries",
        len(scope_map.in_scope),
        len(scope_map.out_of_scope),
    )

    # 3. Initialize or resume session
    session_id = args.resume or str(uuid.uuid4())[:8]
    sess_cfg = config.get("session", {})
    state = SessionState(session_id, sess_cfg.get("output_dir", "session/logs"))
    logger.info("📁 Session: %s", session_id)

    # 4. Build tool registry (scope-enforced)
    tool_registry = build_tool_registry(scope_map, config)
    logger.info("🔧 %d tools registered", len(tool_registry))

    # 5. Recon phase
    compressor = Compressor()
    recon_bridge = ReconBridge(
        binary_path=config.get("recon", {}).get(
            "binary_path", "recon/target/release/recon"
        ),
        default_timeout=config.get("recon", {}).get("default_timeout", 120),
    )

    logger.info("🔍 Running recon on %s", args.target)
    try:
        from urllib.parse import urlparse

        domain = urlparse(args.target).hostname or args.target
        dns_data = recon_bridge.dns_resolve(domain)
        state.save_tool_result("dns_resolve", {"target": domain}, dns_data, domain)
        probe_data = recon_bridge.http_probe(args.target)
        state.save_tool_result(
            "http_probe", {"target": args.target}, probe_data, args.target
        )
    except Exception as e:
        logger.warning("Recon phase failed (binary may not be built): %s", e)

    # 6. Compress recon context
    recon_summary = compressor.compress(state)

    # 7. Plan phase
    planner = Planner(client)
    available_tools = [
        {"name": name, "description": fn.__doc__ or name, "mode": "offensive"}
        for name, fn in tool_registry.items()
    ]
    logger.info("🧠 Generating attack plan...")
    plan = await planner.create_plan(recon_summary, available_tools, scope_map)
    logger.info("📝 Plan: %d steps", len(plan))

    # 8. Execute phase
    executor = Executor(client, tool_registry)
    logger.info("⚡ Executing plan...")
    findings = await executor.run(plan, state)
    logger.info("🎯 Execution complete. %d tool calls made.", len(findings))

    # 9. Report
    reporter = Reporter(config.get("reporting", {}).get("output_dir", "reports"))
    report_path = reporter.generate(args.target, state)
    logger.info("📊 Report saved: %s", report_path)

    print(f"\n{'='*60}")
    print(f" NeuroRift v2 Assessment Complete")
    print(f" Target:   {args.target}")
    print(f" Session:  {session_id}")
    print(f" Findings: {len(state.findings)}")
    print(f" Report:   {report_path}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="NeuroRift v2 — AI-driven multi-language security assessment engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --scope scope.txt --target https://example.com
  python main.py --scope scope.txt --target https://example.com --resume abc12345
        """,
    )
    parser.add_argument(
        "--scope",
        required=True,
        help="Scope file (domain list, H1 markdown, or Bugcrowd JSON)",
    )
    parser.add_argument("--target", required=True, help="Primary target URL")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    parser.add_argument(
        "--resume", default=None, help="Resume a previous session by ID"
    )
    parser.add_argument(
        "--output-dir", default="reports", help="Output directory for reports"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    try:
        asyncio.run(run_assessment(args, config))
    except KeyboardInterrupt:
        logger.info(
            "Interrupted — session state saved. Resume with: --resume <session_id>"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
