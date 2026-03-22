"""
Scan Module for NeuroRift
Handles port scanning and service detection using Nmap.
"""

import asyncio
import logging
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# SECURITY FIX: Use defusedxml instead of xml.etree to prevent XXE attacks
try:
    from defusedxml import ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class ScanModule:
    def __init__(self, base_dir: Path, ai_analyzer: Any):
        self.base_dir = base_dir
        self.ai_analyzer = ai_analyzer
        self.logger = logging.getLogger(__name__)
        self.console = Console()

    async def run_scan(
        self, target: str, output_dir: Optional[Path] = None, use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Run port scan on the target
        """
        self.logger.info("Starting port scan on %s", target)

        results = {"target": target, "ports": [], "ai_analysis": {}, "errors": []}

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                # 1. Run Nmap
                task = progress.add_task(
                    f"Scanning ports for {target} (nmap)...", total=None
                )
                ports = await self._run_nmap(target)
                results["ports"] = ports
                progress.update(task, completed=True)

                if not ports:
                    self.logger.warning("No open ports found on %s", target)
                    return results

                # 2. AI Analysis
                if use_ai:
                    task = progress.add_task("Analyzing results with AI...", total=None)
                    # For AI analyzer, we need the raw output or a string representation
                    nmap_str = self._format_nmap_results(ports)
                    ai_results = await self.ai_analyzer.analyze_nmap_output(nmap_str)
                    results["ai_analysis"] = ai_results
                    progress.update(task, completed=True)

            # Save results if output directory specified
            if output_dir:
                self._save_results(results, output_dir)

            return results

        except Exception as e:
            self.logger.error("Error during scan: %s", e)
            results["errors"].append(str(e))
            return results

    async def _run_nmap(self, target: str) -> List[Dict[str, Any]]:
        """Internal method to run nmap and parse XML"""
        if not self._check_tool("nmap"):
            self.logger.error("Nmap not found. Please install it first.")
            return []

        cmd = ["nmap", "-sV", "-T4", "--max-retries=1", "-oX", "-", target]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                self.logger.error("Nmap error: %s", stderr.decode())
                return []

            root = ET.fromstring(stdout.decode())
            ports = []
            for port in root.findall(".//port"):
                port_data = {
                    "number": port.get("portid"),
                    "protocol": port.get("protocol"),
                    "state": (
                        port.find("state").get("state")
                        if port.find("state") is not None
                        else "unknown"
                    ),
                    "service": (
                        port.find("service").get("name")
                        if port.find("service") is not None
                        else "unknown"
                    ),
                    "product": (
                        port.find("service").get("product")
                        if port.find("service") is not None
                        else ""
                    ),
                    "version": (
                        port.find("service").get("version")
                        if port.find("service") is not None
                        else ""
                    ),
                    "extrainfo": (
                        port.find("service").get("extrainfo")
                        if port.find("service") is not None
                        else ""
                    ),
                }
                ports.append(port_data)
            return ports

        except Exception as e:
            self.logger.error("Error running nmap: %s", e)
            return []

    def _format_nmap_results(self, ports: List[Dict[str, Any]]) -> str:
        """Format port results for AI analysis"""
        lines = ["Nmap scan results:", "PORT     STATE  SERVICE VERSION"]
        for p in ports:
            port_str = f"{p['number']}/{p['protocol']}"
            version_str = f"{p['product']} {p['version']} {p['extrainfo']}".strip()
            lines.append(
                f"{port_str:<8} {p['state']:<6} {p['service']:<7} {version_str}"
            )
        return "\n".join(lines)

    def _check_tool(self, tool_name: str) -> bool:
        """Check if a tool is installed"""
        return subprocess.run(["which", tool_name], capture_output=True).returncode == 0

    def _save_results(self, results: Dict[str, Any], output_dir: Path):
        """Save results to file"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        with open(output_dir / "scan_results.json", "w") as f:
            json.dump(results, f, indent=2)

        # Save Markdown
        with open(output_dir / "scan_report.md", "w") as f:
            f.write(f"# Port Scan Report for {results['target']}\n\n")
            f.write("## Open Ports\n")
            f.write("| Port | Protocol | State | Service | Version |\n")
            f.write("|------|----------|-------|---------|---------|\n")
            for p in results["ports"]:
                version = f"{p['product']} {p['version']}".strip() or "N/A"
                f.write(
                    f"| {p['number']} | {p['protocol']} | {p['state']} | {p['service']} | {p['version']} |\n"
                )

            if results.get("ai_analysis"):
                f.write("\n## AI Security Analysis\n")
                # Handle potentially different AI result formats
                ai = results["ai_analysis"]
                if isinstance(ai, dict):
                    if "summary" in ai:
                        f.write(f"{ai['summary']}\n")
                    if "potential_vulnerabilities" in ai:
                        f.write("\n### Potential Vulnerabilities\n")
                        for v in ai["potential_vulnerabilities"]:
                            f.write(
                                f"- **{v.get('type', 'Unknown')}**: {v.get('description', 'N/A')} (Severity: {v.get('severity', 'N/A')})\n"
                            )
                else:
                    f.write(f"{ai}\n")
