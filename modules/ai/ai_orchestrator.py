import json
import subprocess
import shlex
from pathlib import Path
from modules.ai.ai_integration import LocalAIClient


class AIOrchestrator:
    """
    Manages a multi-step AI reasoning pipeline for complex security tasks.
    It chains specialized prompts for planning, tool selection, and execution.
    """

    def __init__(self, prompt_dir: Path):
        self.prompt_dir = prompt_dir
        self.llm_client = LocalAIClient()
        self.prompts = self._load_prompts()
        self.state = {}

    def _load_prompts(self):
        prompts = {}
        try:
            # SECURITY FIX: Use correct path structure and file names for the nested prompt directories
            base_prompt_dir = self.prompt_dir / "system-prompts-and-models-of-ai-tools"

            # Check what files actually exist and use appropriate fallbacks
            devin_file = base_prompt_dir / "Devin AI/Prompt.txt"
            manus_file = base_prompt_dir / "Manus Agent Tools & Prompt/system.md"
            cursor_file = base_prompt_dir / "Cursor Prompts/prompts.md"

            # Load Devin AI prompt
            if devin_file.exists():
                with open(devin_file, "r") as f:
                    prompts["planner"] = f.read()
            else:
                prompts["planner"] = (
                    "You are a planning AI. Create step-by-step plans for tasks."
                )

            # Load Manus prompt
            if manus_file.exists():
                with open(manus_file, "r") as f:
                    prompts["tool_selector"] = f.read()
            else:
                prompts["tool_selector"] = (
                    "You are a tool selection AI. Choose appropriate tools for tasks."
                )

            # Load Cursor prompt
            if cursor_file.exists():
                with open(cursor_file, "r") as f:
                    prompts["analyst"] = f.read()
            else:
                prompts["analyst"] = (
                    "You are an analysis AI. Analyze results and provide insights."
                )

        except Exception as e:
            print(f"Error: Could not load prompts. {e}")
            # Provide fallback prompts
            prompts = {
                "planner": "You are a planning AI. Create step-by-step plans for tasks.",
                "tool_selector": "You are a tool selection AI. Choose appropriate tools for tasks.",
                "analyst": "You are an analysis AI. Analyze results and provide insights.",
            }
        return prompts

    async def execute_task(self, task_description: str, max_iterations: int = 10):
        """
        Executes a continuous task pipeline: Plan -> Select Tool -> Execute -> Analyze, iterating until complete.
        """
        print("--- AI Autonomous Task Pipeline Initiated ---")
        self.state["history"] = []
        iteration = 0
        current_context = f"Objective: {task_description}\\n"

        while iteration < max_iterations:
            iteration += 1
            print(f"\\n--- Iteration {iteration} ---")

            # 1. Planning Phase (using Devin's prompt)
            plan = await self._planning_phase(current_context)
            print(f"Phase 1: Plan Updated -> {plan[:100]}...")

            if "TASK_COMPLETE" in plan:
                print("Task marked as complete by the planner.")
                break

            # 2. Tool Selection Phase (using Manus' prompt)
            tool_command = await self._tool_selection_phase(task_description, plan)
            print(f"Phase 2: Tool Selected -> {tool_command}")

            if "TASK_COMPLETE" in tool_command:
                print("Task marked as complete by the tool selector.")
                break

            # 3. Wait for Execution (Execution Phase)
            if not tool_command.strip() or tool_command.strip() == "WAIT":
                execution_result = "No command executed. Waiting."
            else:
                execution_result = self._execution_phase(tool_command)
            print(f"Phase 3: Execution Result -> {execution_result[:100]}...")

            # 4. Iterate (Analysis Phase using Cursor's prompt)
            analysis = await self._analysis_phase(execution_result)
            print(f"Phase 4: Analysis Complete -> {analysis[:100]}...")

            # Feed back into context for iterative loop
            current_context += f"\\n--- Iteration {iteration} ---\\nCommand: {tool_command}\\nAnalysis: {analysis}\\n"

            self.state["history"].append(
                {
                    "iteration": iteration,
                    "plan": plan,
                    "command": tool_command,
                    "analysis": analysis,
                }
            )

        print("--- AI Task Pipeline Complete ---")
        return self.state

    async def _planning_phase(self, task_context: str) -> str:
        """Uses the 'planner' prompt to create a high-level strategy."""
        system_prompt = self.prompts.get("planner", "You are a planning AI.")
        user_prompt = f"Context:\\n{task_context}\\nWhat is the next step? If the original objective is completely fulfilled, output exactly 'TASK_COMPLETE'."
        response = await self.llm_client.generate(
            user_prompt, system_prompt=system_prompt
        )
        return str(response)

    async def _tool_selection_phase(self, task: str, plan: str) -> str:
        """Uses the 'tool_selector' prompt to choose the right command."""
        system_prompt = self.prompts.get("tool_selector", "You choose tools.")
        user_prompt = f"Given task '{task}' and plan '{plan}', what specific shell command should be executed next? Output ONLY the command. If finished, output 'TASK_COMPLETE'."
        response = await self.llm_client.generate(
            user_prompt, system_prompt=system_prompt
        )
        return str(response)

    def _execution_phase(self, command: str) -> str:
        """Executes the shell command and returns real output."""
        print(f"Executing: `{command}`")
        try:
            # SECURITY FIX: Use shlex.split to safely parse command without shell=True
            # This prevents command injection while maintaining functionality
            cmd_parts = shlex.split(command)
            result = subprocess.run(
                cmd_parts, capture_output=True, text=True, timeout=600
            )
            if result.returncode == 0:
                return result.stdout
            else:
                return f"[ERROR] Command failed: {result.stderr}"
        except Exception as e:
            return f"[ERROR] Exception during execution: {e}"

    async def _analysis_phase(self, result: str) -> str:
        """Uses the 'analyst' prompt to interpret the results."""
        system_prompt = self.prompts.get("analyst", "You are an analysis AI.")
        user_prompt = f"Analyze the following tool output and provide a summary of key findings and recommendations:\\n\\n{result}"
        response = await self.llm_client.generate(
            user_prompt, system_prompt=system_prompt
        )
        return str(response)
