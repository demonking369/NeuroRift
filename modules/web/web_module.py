"""
Web Module for NeuroRift
Handles web application discovery, technology identification, and directory fuzzing.
"""

import asyncio
import logging
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


class WebModule:
    def __init__(self, base_dir: Path, ai_analyzer: Any):
        self.base_dir = base_dir
        self.ai_analyzer = ai_analyzer
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        self.wordlist = "/usr/share/wordlists/dirb/common.txt"

    async def run_web_discovery(
        self, target: str, output_dir: Optional[Path] = None, use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Run web discovery on the target
        """
        self.logger.info("Starting web discovery on %s (AI: %s)", target, use_ai)

        results = {
            "target": target,
            "technologies": [],
            "directories": [],
            "ai_analysis": {},
            "errors": [],
        }

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                # 1. Technology Identification
                task = progress.add_task(
                    "Identifying technologies (whatweb)...", total=None
                )
                techs = await self._run_whatweb(target)
                results["technologies"] = techs
                progress.update(task, completed=True)

                # 2. Directory Fuzzing
                task = progress.add_task("Fuzzing directories (ffuf)...", total=None)
                dirs = await self._run_ffuf(target)
                results["directories"] = dirs
                progress.update(task, completed=True)

                # 3. AI Analysis
                if use_ai:
                    task = progress.add_task("Analyzing results with AI...", total=None)
                    analysis = await self.analyze_with_ai(target, results)
                    results["ai_analysis"] = analysis
                    progress.update(task, completed=True)
                else:
                    results["ai_analysis"] = {
                        "status": "AI analysis skipped or pending"
                    }

            # Save results
            if output_dir:
                self.save_results(results, output_dir)

            return results

        except Exception as e:
            self.logger.error("Error during web discovery: %s", e)
            results["errors"].append(str(e))
            return results

    async def _run_whatweb(self, target: str) -> List[Dict[str, Any]]:
        """Run whatweb for technology detection"""
        if not self._check_tool("whatweb"):
            self.logger.warning("whatweb not found. Skipping technology detection.")
            return []

        cmd = [
            "whatweb",
            "--color=never",
            "--no-errors",
            "-a",
            "3",
            "--aggression",
            "3",
            target,
        ]
        try:
            # whatweb output is often a bit messy, let's try to get some structured info
            stdout = await self._run_command(" ".join(cmd))
            if not stdout:
                return []

            # Simple parsing for now, whatweb doesn't have a great JSON output by default
            return [{"raw": stdout}]
        except Exception as e:
            self.logger.error("Error running whatweb: %s", e)
            return []

    async def _run_ffuf(self, target: str) -> List[Dict[str, Any]]:
        """Run ffuf for directory fuzzing"""
        if not self._check_tool("ffuf"):
            self.logger.warning("ffuf not found. Skipping directory fuzzing.")
            return []

        if not os.path.exists(self.wordlist):
            self.logger.warning(
                "Wordlist not found at %s. Skipping ffuf.", self.wordlist
            )
            return []

        # Ensure target has protocol and trailing slash for FUZZ
        # Validate target to block shell metacharacters and whitespace
        if re.search(r'[\s;&|`$<>\\()]', target):
            self.logger.error("Invalid characters in target: potential command injection attempt.")
            return []

        url = target
        if "://" not in url:
            url = f"http://{url}"
        if not url.endswith("/"):
            url += "/"
        url += "FUZZ"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_output = temp_file.name

        cmd = [
            "ffuf",
            "-u",
            url,
            "-w",
            self.wordlist,
            "-mc",
            "200,204,301,302,307,401,403",
            "-o",
            temp_output,
            "-of",
            "json",
            "-s",  # silent
        ]

        try:
            # Execute ffuf safely without invoking a shell
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                self.logger.error(
                    "ffuf exited with code %s: %s",
                    process.returncode,
                    stderr.decode(errors="ignore"),
                )

            if os.path.exists(temp_output):
                with open(temp_output, "r") as f:
                    data = json.load(f)
                    results = data.get("results", [])
                    return [
                        {
                            "url": r.get("url"),
                            "status": r.get("status"),
                            "content_length": r.get("length"),
                        }
                        for r in results
                    ]
            return []
        except Exception as e:
            self.logger.error("Error running ffuf: %s", e)
            return []
        finally:
            if os.path.exists(temp_output):
                os.unlink(temp_output)

    async def analyze_with_ai(
        self, target: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze web discovery results using AI"""
        if not self.ai_analyzer:
            return {"error": "AI Analyzer not initialized"}

        # Combine results into a prompt
        prompt = f"""
        Analyze the following web discovery results for target: {target}
        
        Technologies found:
        {json.dumps(results['technologies'], indent=2)}
        
        Directories/Files found:
        {json.dumps(results['directories'], indent=2)}
        
        Provide a security assessment including:
        1. Identified technology stack and known risks.
        2. Interesting directories or files that should be investigated further.
        3. Potential vulnerabilities suggested by the discovered surface.
        4. Recommended next steps for manual testing.
        
        Format the response in JSON:
        {{
            "tech_stack_assessment": "...",
            "interesting_findings": ["...", "..."],
            "suggested_vulnerabilities": ["...", "..."],
            "next_steps": ["...", "..."]
        }}
        """

        system_prompt = "You are a web security expert. Analyze discovery results and provide actionable insights."

        try:
            response = await self.ai_analyzer.llm_client.generate(
                prompt, system_prompt=system_prompt
            )
            if response:
                import re

                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(1))
            return {"error": "Failed to get AI analysis"}
        except Exception as e:
            self.logger.error("Error during AI analysis: %s", e)
            return {"error": str(e)}

    def save_results(self, results: Dict[str, Any], output_dir: Path):
        """Save results to file"""
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_dir / "web_discovery_results.json", "w") as f:
            json.dump(results, f, indent=2)

        with open(output_dir / "web_report.md", "w") as f:
            f.write(f"# Web Discovery Report for {results['target']}\n\n")

            f.write("## Technologies Identified\n")
            if results["technologies"]:
                for tech in results["technologies"]:
                    f.write(f"```\n{tech.get('raw', 'No data')}\n```\n")
            else:
                f.write("No technologies identified.\n")

            f.write("\n## Discovered Directories & Files\n")
            if results["directories"]:
                f.write("| URL | Status | Length |\n")
                f.write("| --- | --- | --- |\n")
                for d in results["directories"]:
                    f.write(f"| {d['url']} | {d['status']} | {d['content_length']} |\n")
            else:
                f.write("No directories or files found.\n")

            f.write("\n## 🤖 AI Security Assessment\n")
            analysis = results.get("ai_analysis", {})
            f.write(
                f"### Tech Stack Assessment\n{analysis.get('tech_stack_assessment', 'N/A')}\n\n"
            )
            f.write("### Interesting Findings\n")
            for finding in analysis.get("interesting_findings", []):
                f.write(f"- {finding}\n")
            f.write("\n### Suggested Vulnerabilities\n")
            for vuln in analysis.get("suggested_vulnerabilities", []):
                f.write(f"- {vuln}\n")
            f.write("\n### Recommended Next Steps\n")
            for step in analysis.get("next_steps", []):
                f.write(f"- {step}\n")

    def _check_tool(self, tool_name: str) -> bool:
        import subprocess

        try:
            subprocess.run(
                ["which", tool_name],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    async def _run_command(self, command: str) -> str:
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode().strip()
