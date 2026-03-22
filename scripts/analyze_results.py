#!/usr/bin/env python3
"""
NeuroRift AI Analysis Script
Analyzes scan results using AI models
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from utils.llm_engine import LLMEngine
from utils.context_builder import ContextBuilder
from utils.notifier import Notifier
from utils.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ResultAnalyzer:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)

        # Initialize components with proper config path
        config_path = base_dir / "config" / "config.json"
        self.config = ConfigManager(config_path)
        self.llm = LLMEngine()
        self.context = ContextBuilder(base_dir)
        self.notifier = Notifier(self.config)

    async def analyze_scan_results(self, results_file: Path):
        """Analyze scan results using AI"""
        try:
            # Load scan results
            with open(results_file) as f:
                results = json.load(f)

            # Add scan results to context
            self.context.add_scan_result("recon", results)

            # Build analysis prompt
            prompt = self.context.build_prompt(
                "recon",
                {
                    "target_info": json.dumps(results["target"], indent=2),
                    "context": self.context._format_context(),
                },
            )

            # Get AI analysis
            analysis = self.llm.query(
                prompt=prompt,
                system_prompt="You are a cybersecurity expert analyzing reconnaissance data.",
            )

            if not analysis:
                logger.error("Failed to get AI analysis")
                return

            # Parse analysis
            try:
                analysis_data = json.loads(analysis)

                # Check for critical findings
                if analysis_data.get("critical_findings"):
                    await self.notifier.notify(
                        "Critical findings detected in scan",
                        "critical",
                        data=analysis_data["critical_findings"],
                    )

                # Save analysis
                output_path = (
                    self.base_dir
                    / "data"
                    / "analysis"
                    / f"analysis_{Path(results_file).stem}.json"
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w") as f:
                    json.dump(analysis_data, f, indent=2)

                logger.info(f"Analysis saved to {output_path}")

                # Generate exploit if critical vulnerability found
                if analysis_data.get("critical_findings"):
                    await self.generate_exploits(analysis_data)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI analysis: {e}")

        except Exception as e:
            logger.error(f"Error analyzing results: {e}")

    async def generate_exploits(self, analysis_data: Dict):
        """Generate exploits for critical findings"""
        from modules.exploit_generator.exploit_generator import ExploitGenerator

        generator = ExploitGenerator(self.base_dir, self.llm)

        for finding in analysis_data.get("critical_findings", []):
            try:
                # Generate exploit
                exploit_data = generator.generate_exploit(
                    cve_data={
                        "cve_id": finding.get("cve_id", "Unknown"),
                        "description": finding.get("description", ""),
                        "affected_software": finding.get("affected_component", ""),
                        "cvss_score": finding.get("severity", "Unknown"),
                    },
                    recon_data={
                        "ip": finding.get("location", ""),
                        "port": finding.get("port", ""),
                        "service": finding.get("service", ""),
                        "version": finding.get("version", ""),
                    },
                )

                if exploit_data and "error" not in exploit_data:
                    # Validate exploit
                    validation = generator.validate_exploit(exploit_data)

                    if validation["syntax_valid"] and validation["has_error_handling"]:
                        # Generate Metasploit module
                        metasploit_module = generator.generate_metasploit_module(
                            exploit_data
                        )

                        # Notify about exploit generation
                        await self.notifier.notify(
                            f"Exploit generated for {finding.get('type', 'Unknown')} vulnerability",
                            "high",
                            data={
                                "finding": finding,
                                "exploit_path": exploit_data.get("file_path"),
                                "metasploit_module": (
                                    str(metasploit_module)
                                    if metasploit_module
                                    else None
                                ),
                                "validation": validation,
                            },
                        )

            except Exception as e:
                logger.error(f"Error generating exploit for finding: {e}")


async def main():
    base_dir = Path(__file__).parent.parent
    analyzer = ResultAnalyzer(base_dir)

    # Find latest scan results
    results_dir = base_dir / "data" / "scan_results"
    if not results_dir.exists():
        logger.error("No scan results found")
        return

    latest_result = max(
        results_dir.glob("recon_*.json"), key=lambda p: p.stat().st_mtime
    )

    # Start notifier
    await analyzer.notifier.start()

    try:
        # Analyze results
        await analyzer.analyze_scan_results(latest_result)
    finally:
        # Stop notifier
        await analyzer.notifier.stop()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
