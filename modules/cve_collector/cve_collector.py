"""
CVE Collector module for NeuroRift
Handles gathering and analyzing CVEs from various sources
"""

import json
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
import hashlib
import time
import re
from urllib.parse import urlparse

from utils.logger import setup_logger
from utils.cli_utils import create_progress, print_results_table
from ai_wrapper.llm_engine import LLMEngine


class CVECollector:
    def __init__(self, base_dir: Path, ai_wrapper: Optional[LLMEngine] = None):
        self.base_dir = base_dir
        self.console = Console()
        self.logger = setup_logger("neurorift.cve_collector")
        self.ai_wrapper = ai_wrapper
        self.data_dir = base_dir / "data" / "cve_feeds"
        self.cache_dir = base_dir / "cache" / "cve_feeds"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # API rate limiting
        self.nvd_rate_limit = 5  # requests per second
        self.github_rate_limit = 30  # requests per hour
        self.last_nvd_request = 0
        self.last_github_request = 0
        self.github_requests_remaining = 30

        # Load API keys if available
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from config"""
        try:
            config_path = self.base_dir / "config" / "api_keys.json"
            if config_path.exists():
                with open(config_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning("Failed to load API keys: %s", e)
            self.api_keys = {}
        return {}

    async def _wait_for_rate_limit(self, api_type: str):
        """Handle API rate limiting"""
        current_time = time.time()

        if api_type == "nvd":
            time_since_last = current_time - self.last_nvd_request
            if time_since_last < (1 / self.nvd_rate_limit):
                await asyncio.sleep((1 / self.nvd_rate_limit) - time_since_last)
            self.last_nvd_request = time.time()

        elif api_type == "github":
            if self.github_requests_remaining <= 0:
                # Wait until rate limit resets (1 hour)
                await asyncio.sleep(3600)
                self.github_requests_remaining = 30
            self.github_requests_remaining -= 1
            self.last_github_request = current_time

    def _get_cache_path(self, source: str, identifier: str) -> Path:
        """Get cache file path for a request"""
        cache_key = hashlib.md5(f"{source}:{identifier}".encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.json"

    async def _get_cached_data(
        self, cache_path: Path, max_age: int = 3600
    ) -> Optional[Dict]:
        """Get cached data if it exists and is not too old"""
        try:
            if cache_path.exists():
                stat = cache_path.stat()
                if time.time() - stat.st_mtime < max_age:
                    async with aiofiles.open(cache_path, "r") as f:
                        return json.loads(await f.read())
        except Exception as e:
            self.logger.warning("Error reading cache: %s", e)
            return None

    async def _save_to_cache(self, cache_path: Path, data: Dict):
        """Save data to cache"""
        try:
            async with aiofiles.open(cache_path, "w") as f:
                await f.write(json.dumps(data))
        except Exception as e:
            self.logger.warning("Error saving to cache: %s", e)

    async def fetch_nvd_feed(self, start_date: Optional[str] = None) -> List[Dict]:
        """Fetch CVE data from NVD feed"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        self.console.print("[bold blue]Fetching NVD CVE feed...[/bold blue]")

        # Check cache first
        cache_path = self._get_cache_path("nvd", start_date)
        cached_data = await self._get_cached_data(
            cache_path, max_age=3600
        )  # 1 hour cache
        if cached_data:
            return cached_data

        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"pubStartDate": f"{start_date}T00:00:00.000", "resultsPerPage": 2000}

        # Add API key if available
        if "nvd" in self.api_keys:
            params["apiKey"] = self.api_keys["nvd"]

        async with aiohttp.ClientSession() as session:
            try:
                await self._wait_for_rate_limit("nvd")
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        cves = data.get("vulnerabilities", [])
                        await self._save_to_cache(cache_path, cves)
                        return cves
                    elif response.status == 429:  # Rate limit exceeded
                        self.logger.warning("NVD rate limit exceeded. Waiting...")
                        await asyncio.sleep(60)
                        return await self.fetch_nvd_feed(start_date)
                    else:
                        self.logger.error("NVD API error: %s", response.status)
                        return []
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error("Error fetching NVD feed: %s", e)
                return []

    async def fetch_exploit_db(self) -> List[Dict]:
        """Fetch exploit data from Exploit-DB"""
        self.console.print("[bold blue]Fetching Exploit-DB data...[/bold blue]")

        # Check cache first
        cache_path = self._get_cache_path("exploitdb", "latest")
        cached_data = await self._get_cached_data(
            cache_path, max_age=86400
        )  # 24 hour cache
        if cached_data:
            return cached_data

        url = "https://raw.githubusercontent.com/offensive-security/exploitdb/master/files_exploits.csv"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        exploits = []

                        # Parse CSV content
                        for line in content.splitlines()[1:]:  # Skip header
                            try:
                                parts = line.split(",")
                                if len(parts) >= 4:
                                    # Extract CVE IDs from description
                                    cve_ids = re.findall(r"CVE-\d{4}-\d+", parts[2])

                                    exploits.append(
                                        {
                                            "id": parts[0],
                                            "file": parts[1],
                                            "description": parts[2],
                                            "date": parts[3],
                                            "author": (
                                                parts[4]
                                                if len(parts) > 4
                                                else "Unknown"
                                            ),
                                            "platform": (
                                                parts[5]
                                                if len(parts) > 5
                                                else "Unknown"
                                            ),
                                            "type": (
                                                parts[6]
                                                if len(parts) > 6
                                                else "Unknown"
                                            ),
                                            "cve_ids": cve_ids,
                                        }
                                    )
                            except:
                                continue

                        await self._save_to_cache(cache_path, exploits)
                        return exploits
                    else:
                        self.logger.error("Exploit-DB fetch error: %s", response.status)
                        return []
            except Exception as e:
                self.logger.error("Error fetching Exploit-DB: %s", e)
                return []

    async def fetch_github_pocs(self, cve_id: str) -> List[Dict]:
        """Search for PoCs on GitHub"""
        self.console.print(
            f"[bold blue]Searching GitHub for {cve_id} PoCs...[/bold blue]"
        )

        # Check cache first
        cache_path = self._get_cache_path("github", cve_id)
        cached_data = await self._get_cached_data(
            cache_path, max_age=86400
        )  # 24 hour cache
        if cached_data:
            return cached_data

        # GitHub API search query
        query = f"{cve_id} poc OR proof of concept OR exploit"
        url = "https://api.github.com/search/code"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "NeuroRift/1.0",
        }

        # Add API key if available
        if "github" in self.api_keys:
            headers["Authorization"] = f"token {self.api_keys['github']}"

        async with aiohttp.ClientSession() as session:
            try:
                await self._wait_for_rate_limit("github")
                async with session.get(
                    url, params={"q": query}, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("items", [])

                        # Process results
                        processed_results = []
                        for result in results:
                            try:
                                # Get file content
                                content_url = result["url"]
                                async with session.get(
                                    content_url, headers=headers
                                ) as content_response:
                                    if content_response.status == 200:
                                        content_data = await content_response.json()
                                        content = content_data.get("content", "")

                                        # Extract relevant information
                                        processed_results.append(
                                            {
                                                "repository": result["repository"][
                                                    "full_name"
                                                ],
                                                "file_path": result["path"],
                                                "url": result["html_url"],
                                                "content": content,
                                                "language": result.get(
                                                    "language", "Unknown"
                                                ),
                                                "stars": result["repository"].get(
                                                    "stargazers_count", 0
                                                ),
                                                "forks": result["repository"].get(
                                                    "forks_count", 0
                                                ),
                                            }
                                        )
                            except Exception as e:
                                self.logger.warning(
                                    "Error processing GitHub result: %s", e
                                )
                                continue

                        await self._save_to_cache(cache_path, processed_results)
                        return processed_results
                    elif response.status == 403:  # Rate limit exceeded
                        self.logger.warning("GitHub rate limit exceeded. Waiting...")
                        await asyncio.sleep(3600)  # Wait 1 hour
                        return await self.fetch_github_pocs(cve_id)
                    else:
                        self.logger.error("GitHub API error: %s", response.status)
                        return []
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                self.logger.error("Error searching GitHub: %s", e)
                return []

    async def analyze_cve(self, cve_data: Dict) -> Dict:
        """Analyze CVE data using AI"""
        if not self.ai_wrapper:
            return cve_data

        prompt = f"""
        Analyze this CVE and provide:
        1. Severity assessment (critical, high, medium, low)
        2. Exploitation complexity (trivial, low, medium, high)
        3. Potential impact (remote code execution, information disclosure, etc.)
        4. Recommended mitigation steps
        5. Related CVEs or similar vulnerabilities
        6. Attack vectors
        7. Affected components
        8. CVSS score analysis
        9. Exploit availability
        10. Patch status
        
        CVE Data:
        {json.dumps(cve_data, indent=2)}
        
        Provide the analysis in JSON format with the following structure:
        {{
            "severity": "string",
            "complexity": "string",
            "impact": "string",
            "mitigation": "string",
            "related_cves": ["string"],
            "attack_vectors": ["string"],
            "affected_components": ["string"],
            "cvss_analysis": {{
                "base_score": "number",
                "temporal_score": "number",
                "environmental_score": "number",
                "vector_string": "string"
            }},
            "exploit_availability": {{
                "public": "boolean",
                "verified": "boolean",
                "sources": ["string"]
            }},
            "patch_status": {{
                "patched": "boolean",
                "patch_date": "string",
                "patch_url": "string"
            }}
        }}
        """

        try:
            # Await the async AI call
            analysis = await self.ai_wrapper.generate(prompt)
            if analysis:
                try:
                    # Try to parse as JSON
                    analysis_json = json.loads(analysis)
                    cve_data["ai_analysis"] = analysis_json
                except json.JSONDecodeError:
                    # Extract JSON if wrapped in markdown
                    json_match = re.search(r"```json\n(.*?)\n```", analysis, re.DOTALL)
                    if json_match:
                        try:
                            cve_data["ai_analysis"] = json.loads(json_match.group(1))
                        except json.JSONDecodeError:
                            cve_data["ai_analysis"] = {"raw_analysis": analysis}
                    else:
                        # If not valid JSON, store as raw text
                        cve_data["ai_analysis"] = {"raw_analysis": analysis}
        except Exception as e:
            self.logger.error("Error analyzing CVE: %s", e)

        return cve_data

    async def search_cves(self, query: str) -> List[Dict[str, Any]]:
        """Search for CVEs based on a query string (e.g., product name and version)"""
        self.logger.info("Searching CVEs for query: %s", query)

        # This is a simplified search that uses the NVD feed we already fetched
        # In a real scenario, this might call an external API or search a local database
        results = []

        # For now, let's fetch the feed and match
        # (Assuming we have a local cache or feed already loaded)
        cves = await self.fetch_nvd_feed()

        # Simple keyword matching
        keywords = query.lower().split()
        for cve in cves:
            desc = (
                cve.get("cve", {}).get("descriptions", [{}])[0].get("value", "").lower()
            )
            if all(k in desc for k in keywords):
                results.append(
                    {
                        "id": cve.get("cve", {}).get("id"),
                        "description": desc,
                        "score": cve.get("cve", {})
                        .get("metrics", {})
                        .get("cvssMetricV31", [{}])[0]
                        .get("cvssData", {})
                        .get("baseScore", "N/A"),
                    }
                )

        return results

    async def collect_cves(self, target_info: Dict) -> Dict[str, Any]:
        """Collect and analyze CVEs for target"""
        self.console.print("[bold blue]Starting CVE collection...[/bold blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            # Fetch NVD feed
            task = progress.add_task("Fetching NVD feed...", total=None)
            cves = await self.fetch_nvd_feed()
            progress.update(task, completed=True)

            # Fetch Exploit-DB data
            task = progress.add_task("Fetching Exploit-DB data...", total=None)
            exploits = await self.fetch_exploit_db()
            progress.update(task, completed=True)

            # Match CVEs to target
            task = progress.add_task("Matching CVEs to target...", total=None)
            matched_cves = []
            for cve in cves:
                if self._matches_target(cve, target_info):
                    matched_cves.append(cve)
            progress.update(task, completed=True)

            # Fetch GitHub PoCs
            task = progress.add_task("Fetching GitHub PoCs...", total=None)
            for cve in matched_cves:
                cve_id = cve.get("cve", {}).get("id")
                if cve_id:
                    pocs = await self.fetch_github_pocs(cve_id)
                    cve["github_pocs"] = pocs
            progress.update(task, completed=True)

            # Analyze CVEs
            task = progress.add_task("Analyzing CVEs...", total=None)
            for cve in matched_cves:
                cve = await self.analyze_cve(cve)
            progress.update(task, completed=True)

            # Save results
            task = progress.add_task("Saving results...", total=None)
            results = {
                "target_info": target_info,
                "cves": matched_cves,
                "exploits": exploits,
                "generated_at": datetime.now().isoformat(),
            }
            await self._save_results(results)
            progress.update(task, completed=True)

            return results

    def _matches_target(self, cve: Dict, target_info: Dict) -> bool:
        """Check if CVE matches target"""
        # Get CPE strings
        cpe_list = []
        for node in cve.get("cve", {}).get("configurations", []):
            for cpe_match in node.get("cpeMatch", []):
                cpe_list.append(cpe_match.get("criteria"))

        # Check each CPE
        for cpe in cpe_list:
            if self._check_cpe_match(cpe, target_info):
                return True

        # Check description for target keywords
        description = (
            cve.get("cve", {}).get("descriptions", [{}])[0].get("value", "").lower()
        )
        target_keywords = [
            target_info.get("name", "").lower(),
            target_info.get("vendor", "").lower(),
            target_info.get("product", "").lower(),
            target_info.get("version", "").lower(),
        ]

        return any(keyword in description for keyword in target_keywords if keyword)

    def _check_cpe_match(self, cpe: str, target_info: Dict) -> bool:
        """Check if CPE string matches target"""
        if not cpe:
            return False

        # Parse CPE
        parts = cpe.split(":")
        if len(parts) < 5:
            return False

        # Check vendor
        if (
            target_info.get("vendor")
            and parts[3] != "*"
            and parts[3].lower() != target_info["vendor"].lower()
        ):
            return False

        # Check product
        if (
            target_info.get("product")
            and parts[4] != "*"
            and parts[4].lower() != target_info["product"].lower()
        ):
            return False

        # Check version
        if target_info.get("version") and parts[5] != "*":
            # Handle version ranges
            if ":" in parts[5]:
                start, end = parts[5].split(":")
                if not (start <= target_info["version"] <= end):
                    return False
            elif parts[5] != target_info["version"]:
                return False

        return True

    async def _save_results(self, results: Dict):
        """Save results to file"""
        # Create results directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = self.data_dir / timestamp
        results_dir.mkdir(exist_ok=True)

        # Save JSON
        json_path = results_dir / "results.json"
        async with aiofiles.open(json_path, "w") as f:
            await f.write(json.dumps(results, indent=2))

        # Save Markdown report
        md_path = results_dir / "report.md"
        async with aiofiles.open(md_path, "w") as f:
            await f.write(self._generate_markdown_report(results))

    def _generate_markdown_report(self, results: Dict) -> str:
        """Generate Markdown report"""
        report = []

        # Add header
        report.append("# CVE Analysis Report")
        report.append(f"Generated: {results['generated_at']}")
        report.append("")

        # Add target info
        report.append("## Target Information")
        for key, value in results["target_info"].items():
            report.append(f"- **{key}**: {value}")
        report.append("")

        # Add findings summary
        report.append("## Findings Summary")
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for cve in results["cves"]:
            severity = cve.get("ai_analysis", {}).get("severity", "info").lower()
            severity_counts[severity] += 1

        report.append("### Severity Distribution")
        for severity, count in severity_counts.items():
            report.append(f"- **{severity.title()}**: {count}")
        report.append("")

        # Add detailed findings
        report.append("## Detailed Findings")
        for cve in results["cves"]:
            cve_id = cve.get("cve", {}).get("id", "Unknown")
            severity = cve.get("ai_analysis", {}).get("severity", "info").lower()

            report.append(f"### {cve_id} ({severity.title()})")

            # Add description
            description = (
                cve.get("cve", {})
                .get("descriptions", [{}])[0]
                .get("value", "No description available")
            )
            report.append(f"**Description**: {description}")

            # Add analysis
            analysis = cve.get("ai_analysis", {})
            if analysis:
                report.append("\n**Analysis**:")
                for key, value in analysis.items():
                    if isinstance(value, list):
                        report.append(f"- **{key}**:")
                        for item in value:
                            report.append(f"  - {item}")
                    elif isinstance(value, dict):
                        report.append(f"- **{key}**:")
                        for k, v in value.items():
                            report.append(f"  - {k}: {v}")
                    else:
                        report.append(f"- **{key}**: {value}")

            # Add PoCs
            pocs = cve.get("github_pocs", [])
            if pocs:
                report.append("\n**Proof of Concepts**:")
                for poc in pocs:
                    report.append(
                        f"- [{poc['repository']}/{poc['file_path']}]({poc['url']})"
                    )

            report.append("")

        return "\n".join(report)
