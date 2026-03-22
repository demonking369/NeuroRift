from typing import List, Dict, Any, Optional
import json
import re
from modules.ai.ai_integration import LocalAIClient
from modules.orchestration.execution_manager import ExecutionManager, ScanRequest
from modules.orchestration.data_models import (
    SessionContext,
    ToolExecutionResult,
    Finding,
)


class NRPlanner:
    def __init__(self, client: LocalAIClient):
        self.llm_client = client

    async def create_plan(
        self, task: str, available_tools: List[Dict]
    ) -> List[ScanRequest]:
        """
        Generates a list of tool executions to achieve the task.
        """
        tools_desc = "\n".join(
            [
                f"- {t['name']}: {t['description']} (Mode: {t.get('mode', 'unknown')})"
                for t in available_tools
            ]
        )

        prompt = f"""
        You are Devin-Planner, an elite security architect for the NeuroRift Framework.
        Your mission is to formulate a robust strategy to accomplish the user's operational goal.
        
        Goal: {task}
        
        Available Tools:
        {tools_desc}
        
        ## OPERATIONAL GUIDELINES
        1. You operate in PLANNING mode. Review the goal and the available tool schemas carefully.
        2. Before formulating your plan, use a <think> tag to reason freely about your strategy, dependencies, and risks.
        3. Do not assume tools exist if they are not listed.
        
        ## OUTPUT FORMAT
        Return a valid JSON array of steps. Each object in the array MUST strictly follow this schema:
        [
            {{
                "think": "<think>Your internal scratchpad reflection and reasoning for this specific step.</think>",
                "tool_name": "exact name from the Available Tools list",
                "target": "target string from the goal context",
                "args": {{"key": "value"}},
                "reasoning": "A concise explanation of why this step is necessary"
            }}
        ]
        """

        response = await self.llm_client.generate(prompt)
        try:
            # Enhanced JSON parsing to handle <think> block pollution inside or outside JSON
            json_match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", response)
            if json_match:
                cleaned = json_match.group(0)
            else:
                cleaned = response.replace("```json", "").replace("```", "").strip()

            plan_data = json.loads(cleaned)

            requests = []
            for step in plan_data:
                # Safely parse the step
                tool_name = step.get("tool_name")
                if not tool_name:
                    continue
                req = ScanRequest(
                    tool_name=tool_name,
                    target=step.get("target", "unknown"),
                    args=step.get("args", {}),
                )
                requests.append(req)
            return requests
        except Exception as e:
            print(f"Error parsing plan: {e}")
            return []


class NROperator:
    def __init__(self, execution_manager: ExecutionManager):
        self.manager = execution_manager

    async def execute_plan(
        self, requests: List[ScanRequest], context: SessionContext
    ) -> List[ToolExecutionResult]:
        results = []
        for req in requests:
            print(f"\n[OPERATOR] Preparing to run: {req.tool_name} on {req.target}")

            # Simulated Execution Wait State (Manus-style)
            # The agent blocks here and receives environment feedback upon completion.
            result = await self.manager.execute_tool(req, context)
            results.append(result)
            if result.status != "success":
                print(f"[OPERATOR] Step failed: {result.error}")
                # Rather than breaking immediately, an autonomous loop would feed this error back.
                # Here we respect the legacy flow but flag the error for the Analyst.
                break
        return results


class NRAnalyst:
    def __init__(self, client: LocalAIClient):
        self.llm_client = client

    async def analyze_results(
        self, results: List[ToolExecutionResult]
    ) -> List[Finding]:
        if not results:
            return []

        context_str = ""
        for res in results:
            context_str += f"Tool: {res.tool_name}\nCommand: {res.command}\nOutput:\n{res.raw_output[:2000]}\n---\n"

        prompt = f"""
        You are Claude-Analyst, a senior security researcher analyzing diagnostic and offensive tool outputs for NeuroRift.
        
        ## EXECUTION RESULTS
        {context_str}
        
        ## OPERATIONAL GUIDELINES
        1. First, evaluate the outputs holistically to identify correlations between different tool results.
        2. Identify explicit vulnerabilities, misconfigurations, and points of interest.
        3. Prioritize findings based on exploitability and impact.
        
        ## OUTPUT FORMAT
        Return a valid JSON array of findings. Each object in the array MUST strictly follow this schema:
        [
            {{
                "think": "<think>Your rigorous technical reasoning about why this constitutes a finding, assessing false positives.</think>",
                "title": "Clear, concise finding name",
                "severity": "CRITICAL, HIGH, MEDIUM, LOW, INFO",
                "description": "Detailed technical explanation",
                "tool_source": "Originating tool name"
            }}
        ]
        """

        response = await self.llm_client.generate(prompt)
        findings = []
        try:
            json_match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", response)
            if json_match:
                cleaned = json_match.group(0)
            else:
                cleaned = response.replace("```json", "").replace("```", "").strip()

            data = json.loads(cleaned)
            for item in data:
                finding = Finding(
                    title=item.get("title", "Unknown Finding"),
                    severity=item.get("severity", "INFO"),
                    description=item.get("description", "No description provided"),
                    tool_source=item.get("tool_source", "AI Analysis"),
                    details=item,
                )
                findings.append(finding)
        except Exception as e:
            print(f"Error parsing analysis: {e}")

        return findings


class NRScribe:
    def __init__(self, client: LocalAIClient):
        self.llm_client = client

    async def generate_report(self, task: str, findings: List[Finding]) -> str:
        findings_text = "\n".join(
            [f"- [{f.severity}] {f.title}: {f.description}" for f in findings]
        )

        prompt = f"""
        You are the NeuroRift Reporting Engine.
        Generate a professional, structured security report for the following engagement.
        
        Task: {task}
        
        Findings:
        {findings_text}
        
        Format the output rigorously in Markdown. You must include:
        1. Executive Summary
        2. Technical Synthesis
        3. Detailed Findings List
        4. Remediation Recommendations
        """
        return await self.llm_client.generate(prompt)
