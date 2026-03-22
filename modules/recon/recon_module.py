#!/usr/bin/env python3
"""
NeuroRift Enhanced Reconnaissance Module
Handles automated reconnaissance with AI-powered analysis
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles
import aiohttp
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class EnhancedReconModule:
    def __init__(
        self, base_dir: Path = None, ai_analyzer: Any = None, config_path: str = None
    ):
        """Initialize the reconnaissance module."""
        self.config = {
            "subfinder": {
                "sources": ["bevigil", "binaryedge", "bufferover", "c99", "censys"],
                "timeout": 30,
            },
            "nmap": {
                "default_flags": ["-sS", "-T4", "--max-retries=1"],
                "stealth_flags": ["-sS", "-T2", "-f"],
                "aggressive_flags": ["-sS", "-T5", "-A"],
            },
            "httpx": {"threads": 50, "timeout": 10, "follow_redirects": True},
            "nuclei": {"severity": ["critical", "high", "medium"]},
        }

        self.base_dir = base_dir or Path.cwd()
        self.ai_analyzer = ai_analyzer
        self.logger = logging.getLogger(__name__)
        self.console = Console()

        if config_path:
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    # Deep merge user config with defaults
                    self.config = self._deep_merge(self.config, user_config)
            except Exception as e:
                self.logger.warning("Failed to load config from %s: %s", config_path, e)
                self.config = self._get_default_config()

    def _deep_merge(self, default, user):
        """Deep merge two dictionaries."""
        result = default.copy()
        for key, value in user.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    async def run_command(self, cmd: List[str], timeout: int = 300) -> str:
        """Run shell command asynchronously"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            return stdout.decode().strip()
        except asyncio.TimeoutError:
            self.logger.error("Command timed out: %s", " ".join(cmd))
            return ""
        except Exception as e:
            self.logger.error("Error running command: %s", e)
            return ""

    async def discover_subdomains(self, domain: str) -> List[str]:
        """Discover subdomains using subfinder"""
        self.console.print("[bold blue]Discovering subdomains...[/bold blue]")

        # Use all available sources instead of restricting to specific ones
        # This allows subfinder to use passive sources that don't require API keys
        cmd = ["subfinder", "-d", domain, "-silent", "-all"]

        output = await self.run_command(cmd)
        if not output:
            self.logger.warning(
                "No output from subfinder for %s. Check if subfinder is installed and configured correctly.",
                domain,
            )
            self.console.print(
                "Warning: No output from subfinder for %s. Check if subfinder is installed and configured correctly."
                % domain
            )
        subdomains = [line.strip() for line in output.splitlines() if line.strip()]
        self.console.print(f"[green]Found {len(subdomains)} subdomains[/green]")
        if not subdomains:
            self.logger.warning(
                "No subdomains found for %s. Check subfinder installation, network, and API keys.",
                domain,
            )
            self.console.print(
                "Warning: No subdomains found for %s. Check subfinder installation, network, and API keys."
                % domain
            )
        return subdomains

    async def probe_web_services(self, subdomains: List[str]) -> List[Dict]:
        """Probe web services using httpx"""
        self.console.print("[bold blue]Probing web services...[/bold blue]")

        # SECURITY FIX: Use tempfile module instead of hardcoded temp paths
        # This prevents path traversal attacks and ensures proper cleanup
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write("\n".join(subdomains))
            temp_file_path = temp_file.name

        try:
            # Run httpx
            cmd = [
                "httpx",
                "-l",
                temp_file_path,
                "-json",
                "-status-code",
                "-title",
                "-tech-detect",
                "-o",
                "-",
            ]

            output = await self.run_command(cmd)
            services = []

            for line in output.splitlines():
                try:
                    service = json.loads(line)
                    services.append(
                        {
                            "url": service.get("url", ""),
                            "status_code": service.get("status-code", 0),
                            "title": service.get("title", ""),
                            "technologies": service.get("technologies", []),
                        }
                    )
                except json.JSONDecodeError:
                    continue

            self.console.print(f"[green]Found {len(services)} web services[/green]")
            return services
        finally:
            # SECURITY FIX: Ensure temp file is always cleaned up
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # File may already be deleted

    async def scan_vulnerabilities(self, web_services: List[Dict]) -> List[Dict]:
        """Scan web services for vulnerabilities using nuclei"""
        self.console.print("[bold blue]Scanning for vulnerabilities...[/bold blue]")

        # SECURITY FIX: Use tempfile module instead of hardcoded temp paths
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write("\n".join(service["url"] for service in web_services))
            temp_file_path = temp_file.name

        try:
            # Run nuclei
            cmd = [
                "nuclei",
                "-l",
                temp_file_path,
                "-json",
                "-severity",
                ",".join(self.config["nuclei"]["severity"]),
                "-silent",
            ]

            output = await self.run_command(cmd)
            vulnerabilities = []

            for line in output.splitlines():
                try:
                    vuln = json.loads(line)
                    vulnerabilities.append(
                        {
                            "url": vuln.get("url", ""),
                            "type": vuln.get("type", ""),
                            "severity": vuln.get("severity", ""),
                            "description": vuln.get("description", ""),
                            "template": vuln.get("template", ""),
                        }
                    )
                except json.JSONDecodeError:
                    continue

            self.console.print(
                f"[green]Found {len(vulnerabilities)} potential vulnerabilities[/green]"
            )
            return vulnerabilities
        finally:
            # SECURITY FIX: Ensure temp file is always cleaned up
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # File may already be deleted

    async def run_recon(
        self, target: str, output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Run comprehensive reconnaissance on target"""
        self.console.print(
            f"[bold blue]Starting reconnaissance on {target}[/bold blue]"
        )

        # SECURITY FIX: Ensure output_dir is a Path object
        if output_dir is None:
            output_dir = self.base_dir / "recon_results" / target.replace(".", "_")
        elif isinstance(output_dir, str):
            output_dir = Path(output_dir)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run reconnaissance tasks sequentially for now
        # SECURITY FIX: Fixed async/await issues and added missing methods
        try:
            subdomains = await self.discover_subdomains(target)
            web_services = await self.probe_web_services(subdomains)
            vulnerabilities = await self.scan_vulnerabilities(web_services)

            # Generate AI analysis
            ai_analysis = await self._analyze_results(
                target, subdomains, web_services, vulnerabilities
            )

            # Prepare results
            results = {
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "subdomains": subdomains,
                "web_services": web_services,
                "vulnerabilities": vulnerabilities,
                "ai_analysis": ai_analysis,
            }

            # Save results
            await self._save_results(results, output_dir)

            return results

        except Exception as e:
            self.logger.error("Error during reconnaissance: %s", e)
            return {
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "subdomains": [],
                "web_services": [],
                "vulnerabilities": [],
                "ai_analysis": {},
            }

    async def _analyze_results(
        self,
        target: str,
        subdomains: List[str],
        web_services: List[Dict],
        vulnerabilities: List[Dict],
    ) -> Dict:
        """Analyze results using AI"""
        self.console.print("[bold blue]Analyzing results with AI...[/bold blue]")

        # Prepare data for AI analysis
        analysis_data = {
            "target": target,
            "subdomain_count": len(subdomains),
            "web_service_count": len(web_services),
            "vulnerability_count": len(vulnerabilities),
            "critical_findings": [],
            "recommendations": [],
        }

        # Analyze vulnerabilities
        if vulnerabilities:
            vuln_summary = "\n".join(
                [
                    f"- {v['type']} ({v['severity']}): {v['description']}"
                    for v in vulnerabilities
                ]
            )

            prompt = f"""
            Analyze these security findings for {target}:
            
            {vuln_summary}
            
            Provide:
            1. Critical findings that need immediate attention
            2. Recommended next steps for exploitation
            3. Potential attack chains
            """

            ai_response = self.ai_analyzer.llm_client.generate(prompt)
            if ai_response:
                try:
                    analysis = json.loads(ai_response)
                    analysis_data.update(analysis)
                except:
                    # If JSON parsing fails, use raw response
                    analysis_data["raw_analysis"] = ai_response

        return analysis_data

    async def _save_results(self, results: Dict, output_dir: Path):
        """Save results in multiple formats"""
        # Save JSON
        json_path = output_dir / "results.json"
        try:
            async with aiofiles.open(json_path, "w") as f:
                await f.write(json.dumps(results, indent=2))
        except (aiofiles.OSError, aiofiles.IOError) as e:
            self.logger.error("Error writing results: %s", e)

        # Generate Markdown report
        md_path = output_dir / "report.md"
        try:
            async with aiofiles.open(md_path, "w") as f:
                await f.write(
                    f"""# NeuroRift Reconnaissance Report

## Target: {results['target']}
## Scan Time: {results['timestamp']}

### Summary
- Subdomains Found: {len(results['subdomains'])}
- Web Services: {len(results['web_services'])}
- Vulnerabilities: {len(results['vulnerabilities'])}

### Subdomains
{chr(10).join(f'- {subdomain}' for subdomain in results['subdomains'])}

### Web Services
{chr(10).join(f'- {service["url"]} ({service["status_code"]})' for service in results['web_services'])}

### Vulnerabilities
{chr(10).join(f'- {vuln["type"]} ({vuln["severity"]}): {vuln["description"]}' for vuln in results['vulnerabilities'])}

### AI Analysis
{json.dumps(results['ai_analysis'], indent=2)}
"""
                )
        except (aiofiles.OSError, aiofiles.IOError) as e:
            self.logger.error("Error writing results: %s", e)

        self.console.print(f"[green]Results saved to: {output_dir}[/green]")
