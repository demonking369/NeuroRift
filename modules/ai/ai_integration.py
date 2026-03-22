#!/usr/bin/env python3
"""
NeuroRift AI Integration Module
Handles llama.cpp integration, prompt engineering, and AI-powered analysis
"""

import json
import os
import httpx
import logging
from typing import Dict, List, Optional, Any
import time
import re
from pathlib import Path
import asyncio
import ctypes

try:
    from duckduckgo_search import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

from ai_wrapper.llama_client import LlamaClient


class LocalAIClient:
    def __init__(self, base_url: str = "http://localhost:8080/v1"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.client = LlamaClient(base_url)
        self.ai_enabled = os.getenv("AI_ENABLED", "true").lower() == "true"
        self.model = "hermes-2-pro-mistral-7b"

    async def is_available(self) -> bool:
        """Check if llama.cpp service is running"""
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(f"{self.base_url}/models")
                return response.status_code == 200
        except httpx.RequestError:
            return False

    async def ensure_service_running(self) -> bool:
        """Check if service is running. Warn to start script if not."""
        if await self.is_available():
            return True

        self.logger.warning(
            "llama.cpp service not available. Please run ./scripts/start_llama.sh"
        )
        return False

    async def list_models(self) -> List[Dict]:
        """List available models"""
        return [{"name": self.model}]

    def pull_model(self, model: str) -> bool:
        """Instructs user to use the download script"""
        self.logger.error("Auto-pull removed. Please use ./scripts/download_model.sh")
        return False

    async def generate(
        self,
        prompt: str,
        model: str = None,
        system_prompt: str = None,
        format: str = None,
    ) -> Optional[str]:
        """Generate text using LlamaClient"""
        if not self.ai_enabled:
            return None

        if not await self.ensure_service_running():
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Add explicit instructions for JSON if requested
        if format == "json":
            messages[-1]["content"] += "\nEnsure the output is valid JSON."

        res = await self.client.generate_chat(messages, model=model or self.model)
        if res and res.get("type") == "text":
            return res.get("content")
        return None

    async def query(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Wrapper for compatibility with modules expecting .query()"""
        return await self.generate(prompt=prompt, system_prompt=system_prompt)

    async def get_best_model(self) -> Optional[str]:
        """Get the best available model"""
        return self.model


# Load the shared library
parser_lib_path = Path(__file__).parent / "utils" / "c_parser" / "libparser.so"

# SECURITY FIX: Add fallback mechanism for missing C library
# This prevents the application from crashing when the native library is not compiled
try:
    c_parser = ctypes.CDLL(str(parser_lib_path))
    # Define the function signature for type safety
    c_parser.parse_nuclei_output.argtypes = [ctypes.c_char_p]
    c_parser.parse_nuclei_output.restype = ctypes.c_char_p
    C_PARSER_AVAILABLE = True
except (OSError, FileNotFoundError):
    # Fallback to pure Python implementation when C library is not available
    c_parser = None
    C_PARSER_AVAILABLE = False
    import logging

    logging.getLogger(__name__).warning(
        "C parser library not found. Using Python fallback."
    )


class AIAnalyzer:
    def __init__(self, llm_client: LocalAIClient):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)

    async def analyze_nmap_output(self, nmap_output: str) -> Dict[str, Any]:
        """Analyze nmap scan results using AI"""
        system_prompt = """You are a cybersecurity expert analyzing nmap scan results. 
        Identify potential vulnerabilities, interesting services, and security issues.
        Provide structured analysis in JSON format with severity levels."""

        prompt = f"""
        Analyze this nmap scan output and identify potential security issues:
        
        {nmap_output}
        
        Provide analysis in this JSON format:
        {{
            "summary": "Brief overview",
            "high_risk_ports": ["port:service pairs that are high risk"],
            "interesting_services": ["notable services found"],
            "potential_vulnerabilities": [
                {{
                    "port": "port number",
                    "service": "service name",
                    "vulnerability": "description",
                    "severity": "low/medium/high/critical",
                    "recommendation": "what to investigate"
                }}
            ],
            "next_steps": ["recommended follow-up actions"]
        }}
        """

        response = await self.llm_client.generate(prompt, system_prompt=system_prompt)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Extract JSON if wrapped in markdown
                json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        pass

        return {"error": "Failed to analyze nmap output", "raw_response": response}

    async def perform_web_search(self, query: str, max_results: int = 3) -> str:
        """Perform a web search to augment AI context"""
        if not DDGS_AVAILABLE:
            return "Web search unavailable (duckduckgo-search not installed)."

        try:
            self.logger.info(f"Performing web search for: {query}")
            results = DDGS().text(query, max_results=max_results)
            if not results:
                return "No results found."

            formatted_results = "Web Search Results:\n"
            for i, r in enumerate(results, 1):
                formatted_results += (
                    f"{i}. {r['title']}\n   {r['body']}\n   Source: {r['href']}\n\n"
                )
            return formatted_results
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return f"Web search failed: {e}"

    async def generate_exploit_code(self, vulnerability_info: Dict) -> Dict[str, Any]:
        """Generate exploit code based on vulnerability information"""
        prompt = f"""
        Generate a safe, educational exploit for the following vulnerability:
        {json.dumps(vulnerability_info, indent=2)}
        
        Focus on:
        1. Identification of the vulnerable component.
        2. Proof of Concept (PoC) code in Python.
        3. Clear comments explaining each step.
        4. Safety measures and authorization checks.
        
        Provide the result in this JSON format:
        {{
            "vulnerability": "Name",
            "exploit_code": "Python code here",
            "explanation": "Brief description of how it works",
            "safety_warning": "Warning about usage"
        }}
        """

        response = await self.llm_client.generate(prompt)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

        return {"error": "Failed to generate exploit", "raw_response": response}

    async def analyze_web_response(
        self, url: str, response_data: Dict
    ) -> Dict[str, Any]:
        """Analyze web service response for vulnerabilities"""
        system_prompt = """You are a web application security expert.
        Analyze HTTP responses for potential vulnerabilities and security issues."""

        headers = response_data.get("headers", {})
        content = response_data.get("content", "")[:2000]  # Limit content length

        prompt = f"""
        Analyze this web service for security issues:
        
        URL: {url}
        Status Code: {response_data.get('status_code')}
        Headers: {json.dumps(headers, indent=2)}
        Content (first 2000 chars): {content}
        
        Look for:
        - Missing security headers
        - Information disclosure
        - Potential injection points
        - Authentication issues
        - Technology stack vulnerabilities
        
        Provide JSON analysis:
        {{
            "security_headers": {{
                "missing": ["list of missing security headers"],
                "present": ["list of present security headers"]
            }},
            "information_disclosure": ["any leaked information"],
            "potential_vulnerabilities": [
                {{
                    "type": "vulnerability type",
                    "description": "detailed description",
                    "severity": "low/medium/high/critical",
                    "location": "where found"
                }}
            ],
            "technology_stack": ["detected technologies"],
            "recommendations": ["security recommendations"]
        }}
        """

        response = await self.llm_client.generate(prompt, system_prompt=system_prompt)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        pass

        return {"error": "Failed to analyze web response", "raw_response": response}

    async def fix_broken_tool(
        self, tool_name: str, error_output: str, source_code: str = None
    ) -> str:
        """Generate fixes for broken security tools"""
        system_prompt = """You are a DevOps engineer specializing in fixing broken security tools.
        Analyze errors and provide working solutions."""

        prompt = f"""
        This security tool is broken and needs fixing:
        
        Tool: {tool_name}
        Error Output: {error_output}
        Source Code (if available): {source_code[:1000] if source_code else 'Not provided'}
        
        Analyze the error and provide:
        1. Root cause analysis
        2. Step-by-step fix instructions
        3. Modified code if needed
        4. Alternative solutions
        5. Prevention measures
        
        Focus on common issues like:
        - Dependency problems
        - API changes
        - Python version compatibility
        - Missing environment variables
        - Network/permission issues
        """

        response = await self.llm_client.generate(prompt, system_prompt=system_prompt)
        return response or "# Failed to generate fix"

    async def prioritize_vulnerabilities(
        self, vulnerabilities: List[Dict]
    ) -> List[Dict]:
        """Use AI to prioritize vulnerabilities by exploitability and impact"""
        system_prompt = """You are a penetration tester prioritizing vulnerabilities.
        Rank vulnerabilities by exploitability and business impact."""

        prompt = f"""
        Prioritize these vulnerabilities for testing:
        
        {json.dumps(vulnerabilities, indent=2)}
        
        Consider:
        - Ease of exploitation
        - Potential impact
        - Likelihood of success
        - Chaining possibilities
        
        Return prioritized list with scores (1-10) and reasoning:
        {{
            "prioritized_vulnerabilities": [
                {{
                    "original_index": 0,
                    "exploitability_score": 8,
                    "impact_score": 9,
                    "overall_priority": 8.5,
                    "reasoning": "why this is high priority",
                    "exploitation_difficulty": "easy/medium/hard",
                    "recommended_tools": ["tools to use"]
                }}
            ]
        }}
        """

        response = await self.llm_client.generate(prompt, system_prompt=system_prompt)
        if response:
            try:
                result = json.loads(response)
                return result.get("prioritized_vulnerabilities", vulnerabilities)
            except:
                pass

        return vulnerabilities

    def analyze_nuclei_output(self, nuclei_json_output: str) -> Dict[str, Any]:
        """Analyze nuclei output using the high-speed C parser."""

        if C_PARSER_AVAILABLE and c_parser:
            # Use the high-speed C parser when available
            raw_summary = c_parser.parse_nuclei_output(
                nuclei_json_output.encode("utf-8")
            )
            summary_str = raw_summary.decode("utf-8")
        else:
            # SECURITY FIX: Fallback to pure Python implementation
            # This ensures the application works even without the native library
            try:
                import json

                data = json.loads(nuclei_json_output)
                critical_count = sum(
                    1
                    for item in data
                    if item.get("info", {}).get("severity") == "critical"
                )
                summary_str = json.dumps({"critical_findings": critical_count})
            except (json.JSONDecodeError, TypeError):
                summary_str = '{"error": "Failed to parse nuclei output"}'

        try:
            return json.loads(summary_str)
        except json.JSONDecodeError:
            return {"error": "Failed to parse summary from parser"}


class AIOrchestrator:
    """
    Manages a multi-step AI reasoning pipeline for complex security tasks.
    It chains specialized prompts for planning, tool selection, and execution.
    """

    def __init__(self, prompt_dir: Path):
        self.prompt_dir = prompt_dir
        self.llm_client = LocalAIClient()
        self.analyzer = AIAnalyzer(self.llm_client)
        self.prompts = self._load_prompts()
        self.state = {}

    def _load_prompts(self):
        """Loads the specialized AI prompts from the prompt directory."""
        prompts = {}
        # The prompt_dir is /home/arun/tools/Custom_T_1/NeuroRift/prompts/system_prompts
        try:
            # Devin-style planning prompt
            planner_path = self.prompt_dir / "Devin AI" / "Prompt.txt"
            if planner_path.exists():
                with open(planner_path, "r") as f:
                    prompts["planner"] = f.read()
            else:
                prompts["planner"] = "You are an expert security planner."

            # Manus-style tool selection prompt
            tool_path = self.prompt_dir / "Manus Agent Tools & Prompt" / "Prompt.txt"
            if tool_path.exists():
                with open(tool_path, "r") as f:
                    prompts["tool_selector"] = f.read()
            else:
                prompts["tool_selector"] = (
                    "You are an expert at selecting the best security tool for a task."
                )

            # Cursor-style code/analysis prompt
            analyst_path = self.prompt_dir / "Cursor Prompts" / "Cursor Prompts.txt"
            # Checking common child in Cursor Prompts
            if not analyst_path.exists():
                # Fallback to the first .txt file found if possible, or a default
                analyst_path = self.prompt_dir / "Cursor Prompts" / "System Prompt.txt"

            if analyst_path.exists():
                with open(analyst_path, "r") as f:
                    prompts["analyst"] = f.read()
            else:
                prompts["analyst"] = (
                    "You are a senior security researcher analyzing results."
                )

        except Exception as e:
            logging.getLogger(__name__).error(f"Error loading specialized prompts: {e}")
            # Ensure we have defaults if everything fails
            prompts.setdefault("planner", "You are an expert security planner.")
            prompts.setdefault(
                "tool_selector",
                "You are an expert at selecting the best security tool.",
            )
            prompts.setdefault("analyst", "You are a senior security researcher.")

        return prompts

    async def execute_task(self, task_description: str):
        """
        Executes a full task pipeline: Plan -> Select Tool -> Execute -> Analyze.
        """
        print("--- AI Task Pipeline Initiated ---")

        # 1. Planning Phase (using specialized prompt)
        plan = await self._planning_phase(task_description)
        self.state["plan"] = plan
        print(f"Phase 1: Plan Created -> {plan}")

        # 2. Tool Selection Phase (using specialized prompt)
        tool_command = await self._tool_selection_phase(task_description, plan)
        self.state["tool_command"] = tool_command
        print(f"Phase 2: Tool Selected -> {tool_command}")

        # 3. Execution Phase (simulated)
        execution_result = self._execution_phase(tool_command)
        self.state["execution_result"] = execution_result
        print(f"Phase 3: Execution Result -> {execution_result[:100]}...")

        # 4. Analysis Phase (using specialized prompt)
        analysis = await self._analysis_phase(execution_result)
        self.state["analysis"] = analysis
        print(f"Phase 4: Analysis Complete -> {analysis}")

        print("--- AI Task Pipeline Complete ---")
        return self.state

    async def _planning_phase(self, task: str) -> str:
        """Uses the 'planner' prompt to create a high-level strategy."""
        system_prompt = self.prompts["planner"]
        user_prompt = f"Create a step-by-step plan for the following task: {task}"
        response = await self.llm_client.generate(
            user_prompt, system_prompt=system_prompt
        )
        return response

    async def _tool_selection_phase(self, task: str, plan: str) -> str:
        """Uses the 'tool_selector' prompt to choose the right command."""
        system_prompt = self.prompts["tool_selector"]
        user_prompt = f"Given the task '{task}' and the plan '{plan}', what is the exact shell command to execute next? Only output the command."
        response = await self.llm_client.generate(
            user_prompt, system_prompt=system_prompt
        )
        return response

    def _execution_phase(self, command: str) -> str:
        """Simulates running the command and returns mock output."""
        print(f"Simulating execution of: `{command}`")
        if "nmap" in command:
            return "Starting Nmap 7.92 ... Nmap scan report for example.com (93.184.216.34)\nHost is up (0.011s latency).\nNot shown: 998 filtered tcp ports\nPORT    STATE SERVICE\n80/tcp  open  http\n443/tcp open  https"
        return "Command executed successfully. No output."

    async def _analysis_phase(self, result: str) -> str:
        """Uses the 'analyst' prompt to interpret the results."""
        system_prompt = self.prompts["analyst"]
        user_prompt = f"Analyze the following tool output and provide a summary of key findings and recommendations:\n\n{result}"
        response = await self.llm_client.generate(
            user_prompt, system_prompt=system_prompt
        )
        return response


# CLI interface for AI module
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NeuroRift AI Module")
    parser.add_argument(
        "--test-connection", action="store_true", help="Test llama.cpp connection"
    )
    parser.add_argument("--pull-model", help="Pull a specific model")
    parser.add_argument(
        "--list-models", action="store_true", help="List available models"
    )
    parser.add_argument("--analyze-nmap", help="Analyze nmap output file")
    parser.add_argument(
        "--ai-pipeline",
        action="store_true",
        help="Enable the advanced multi-prompt AI pipeline.",
    )
    parser.add_argument(
        "--prompt-dir",
        help="Directory for the AI pipeline prompts.",
        default="prompts/system_prompts",
    )

    args = parser.parse_args()

    orchestrator = AIOrchestrator(Path(args.prompt_dir))

    if args.test_connection:
        if orchestrator.llm_client.is_available():
            print("✓ AI system ready")
        else:
            print("✗ AI system not available")

    elif args.pull_model:
        if orchestrator.llm_client.pull_model(args.pull_model):
            print(f"✓ Model {args.pull_model} pulled successfully")
        else:
            print(f"✗ Failed to pull model {args.pull_model}")

    elif args.list_models:
        models = orchestrator.llm_client.list_models()
        print("Available models:")
        for model in models:
            print(f"  - {model['name']}")

    elif args.analyze_nmap:
        with open(args.analyze_nmap, "r") as f:
            content = f.read()
        result = orchestrator.analyzer.analyze_nmap_output(content)
        print(json.dumps(result, indent=2))

    # Handle AI Pipeline Mode
    if args.ai_pipeline:
        if not args.target:
            print(
                "Error: A target is required for AI pipeline mode, e.g., --target 'scan example.com'"
            )

        prompt_path = Path(args.prompt_dir)
        if not prompt_path.exists():
            print(f"Error: Prompt directory not found at '{prompt_path}'")

        orchestrator = AIOrchestrator(prompt_path)
        asyncio.run(
            orchestrator.execute_task(f"Perform a security scan on {args.target}")
        )
