#!/usr/bin/env python3
"""
NeuroRift Orchestrator
Central orchestration engine for multi-agent security operations.

Contributors:
- NeuroRift Core Team
- x1xhlol (system-prompts-and-models-of-ai-tools)
- SimStudioAI (conceptual orchestration)
- Anti-Gravity AI
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from modules.ai.mode_governor import ModeGovernor, OperationalMode
from modules.ai.task_memory import TaskMemory
from modules.ai.agent_context import AgentContext


class AgentType(Enum):
    """Agent types in the orchestration system"""

    PLANNER = "planner"
    OPERATOR = "operator"
    ANALYST = "analyst"
    SCRIBE = "scribe"


class OrchestrationStatus(Enum):
    """Status of orchestration"""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    ANALYZING = "analyzing"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


class NeuroRiftXOrchestrator:
    """
    Central orchestration engine for NeuroRift multi-agent system.

    Manages the lifecycle of security assessment operations by coordinating
    multiple specialized agents (Planner, Operator, Analyst, Scribe).
    """

    def __init__(self, config_path: str = "configs/neurorift_x_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.mode_governor = ModeGovernor(config_path)
        self.task_memory = TaskMemory()
        self.agent_context = AgentContext()

        # Orchestration state
        self.status = OrchestrationStatus.IDLE
        self.current_agent: Optional[AgentType] = None
        self.current_task_id: Optional[str] = None
        self.orchestration_cycle = 0
        self.max_cycles = self.config.get("orchestration", {}).get(
            "max_orchestration_cycles", 5
        )

        # Agent flow configuration
        self.agent_flow = [
            AgentType.PLANNER,
            AgentType.OPERATOR,
            AgentType.ANALYST,
            AgentType.SCRIBE,
        ]

        self.logger.info("NeuroRift Orchestrator initialized")

    def _load_config(self) -> Dict:
        """Load NeuroRift configuration"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration: {e}")
            raise

    def initialize_task(self, user_request: str, mode: str, target: str) -> str:
        """
        Initialize a new security assessment task.

        Args:
            user_request: User's security assessment request
            mode: Operational mode ('offensive' or 'defensive')
            target: Target domain/IP

        Returns:
            Task ID
        """
        # Set operational mode
        self.mode_governor.set_mode(mode)

        # Create task
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_task_id = task_id

        # Initialize task memory
        task_data = {
            "task_id": task_id,
            "user_request": user_request,
            "mode": mode,
            "target": target,
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "orchestration_cycle": 0,
        }

        self.task_memory.create_task(task_id, task_data)

        # Initialize agent context
        self.agent_context.initialize(
            task_id, {"user_request": user_request, "mode": mode, "target": target}
        )

        self.logger.info(
            f"Task {task_id} initialized in {mode.upper()} mode for target: {target}"
        )
        return task_id

    def execute_task(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a security assessment task through the agent pipeline.

        Args:
            task_id: Task ID to execute (uses current task if None)

        Returns:
            Execution results
        """
        if task_id:
            self.current_task_id = task_id

        if not self.current_task_id:
            raise ValueError("No task ID specified")

        self.logger.info(f"Starting orchestration for task: {self.current_task_id}")

        results = {
            "task_id": self.current_task_id,
            "status": "in_progress",
            "agent_outputs": {},
        }

        try:
            # Execute agent flow
            for agent_type in self.agent_flow:
                self.logger.info(f"Executing agent: {agent_type.value}")
                self.current_agent = agent_type
                self.status = self._get_status_for_agent(agent_type)

                # Execute agent
                agent_output = self._execute_agent(agent_type)
                results["agent_outputs"][agent_type.value] = agent_output

                # Update task memory
                self.task_memory.update_task(
                    self.current_task_id, {f"{agent_type.value}_output": agent_output}
                )

                # Check for errors
                if agent_output.get("status") == "failed":
                    self.logger.error(f"Agent {agent_type.value} failed")
                    results["status"] = "failed"
                    results["error"] = agent_output.get("error")
                    break

                # Check for human approval requirement
                if agent_output.get("requires_human_approval"):
                    self.status = OrchestrationStatus.AWAITING_APPROVAL
                    results["status"] = "awaiting_approval"
                    results["approval_request"] = agent_output.get("approval_request")
                    return results

            # All agents completed successfully
            self.status = OrchestrationStatus.COMPLETED
            results["status"] = "completed"

            # Update task memory
            self.task_memory.update_task(
                self.current_task_id,
                {"status": "completed", "completed_at": datetime.now().isoformat()},
            )

            self.logger.info(f"Task {self.current_task_id} completed successfully")

        except Exception as e:
            self.logger.error(f"Orchestration error: {e}", exc_info=True)
            self.status = OrchestrationStatus.FAILED
            results["status"] = "failed"
            results["error"] = str(e)

        return results

    def _execute_agent(self, agent_type: AgentType) -> Dict[str, Any]:
        """
        Execute a specific agent.

        Args:
            agent_type: Type of agent to execute

        Returns:
            Agent output
        """
        # Get agent configuration
        agent_config = self.config.get("agents", {}).get(agent_type.value, {})

        # Load agent prompt
        prompt_file = agent_config.get("prompt_file")
        if prompt_file:
            prompt = self._load_prompt(prompt_file)
        else:
            prompt = ""

        # Get agent context
        context = self.agent_context.get_context(agent_type.value)

        # Execute agent based on type
        if agent_type == AgentType.PLANNER:
            return self._execute_planner(prompt, context)
        elif agent_type == AgentType.OPERATOR:
            return self._execute_operator(prompt, context)
        elif agent_type == AgentType.ANALYST:
            return self._execute_analyst(prompt, context)
        elif agent_type == AgentType.SCRIBE:
            return self._execute_scribe(prompt, context)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def _execute_planner(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Execute NR Planner agent"""
        self.logger.info("NR Planner: Creating execution plan")

        # TODO: Integrate with actual LLM
        # For now, return a placeholder plan
        plan = {
            "plan_id": f"plan_{self.current_task_id}",
            "objective": context.get("user_request"),
            "mode": context.get("mode"),
            "target": context.get("target"),
            "status": "completed",
            "steps": [
                {
                    "step_id": 1,
                    "description": "Enumerate subdomains",
                    "agent": "operator",
                    "tool": "subfinder",
                    "requires_human_approval": False,
                }
            ],
        }

        # Store plan in agent context
        self.agent_context.set_context("planner", plan)

        return plan

    def _execute_operator(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Execute NR Operator agent"""
        self.logger.info("NR Operator: Executing plan")

        # Get plan from Planner
        plan = self.agent_context.get_context("planner")

        # TODO: Execute actual commands
        # For now, return placeholder results
        results = {
            "execution_id": f"exec_{self.current_task_id}",
            "status": "completed",
            "executed_steps": len(plan.get("steps", [])),
            "outputs": [],
        }

        # Store results in agent context
        self.agent_context.set_context("operator", results)

        return results

    def _execute_analyst(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Execute NR Analyst agent"""
        self.logger.info("NR Analyst: Analyzing results")

        # Get execution results from Operator
        exec_results = self.agent_context.get_context("operator")

        # TODO: Perform actual analysis
        # For now, return placeholder analysis
        analysis = {
            "analysis_id": f"analysis_{self.current_task_id}",
            "status": "completed",
            "findings": [],
            "summary": {
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }

        # Store analysis in agent context
        self.agent_context.set_context("analyst", analysis)

        return analysis

    def _execute_scribe(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Execute NR Scribe agent"""
        self.logger.info("NR Scribe: Generating report")

        # Get analysis from Analyst
        analysis = self.agent_context.get_context("analyst")

        # TODO: Generate actual report
        # For now, return placeholder report
        report = {
            "report_id": f"report_{self.current_task_id}",
            "status": "completed",
            "format": "markdown",
            "path": f"~/.neurorift/reports/{self.current_task_id}.md",
        }

        # Store report in agent context
        self.agent_context.set_context("scribe", report)

        return report

    def _load_prompt(self, prompt_file: str) -> str:
        """Load agent prompt from file"""
        try:
            with open(prompt_file, "r") as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning(f"Prompt file not found: {prompt_file}")
            return ""

    def _get_status_for_agent(self, agent_type: AgentType) -> OrchestrationStatus:
        """Get orchestration status for agent type"""
        status_map = {
            AgentType.PLANNER: OrchestrationStatus.PLANNING,
            AgentType.OPERATOR: OrchestrationStatus.EXECUTING,
            AgentType.ANALYST: OrchestrationStatus.ANALYZING,
            AgentType.SCRIBE: OrchestrationStatus.REPORTING,
        }
        return status_map.get(agent_type, OrchestrationStatus.IDLE)

    def get_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return {
            "status": self.status.value,
            "current_agent": self.current_agent.value if self.current_agent else None,
            "current_task_id": self.current_task_id,
            "orchestration_cycle": self.orchestration_cycle,
            "mode": (
                self.mode_governor.current_mode.value
                if self.mode_governor.current_mode
                else None
            ),
        }

    def resume_task(self, task_id: str) -> Dict[str, Any]:
        """Resume a paused or failed task"""
        self.logger.info(f"Resuming task: {task_id}")
        self.current_task_id = task_id

        # Load task from memory
        task_data = self.task_memory.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task not found: {task_id}")

        # Restore mode
        self.mode_governor.set_mode(task_data.get("mode"))

        # Continue execution
        return self.execute_task(task_id)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize orchestrator
    orchestrator = NeuroRiftXOrchestrator()

    # Initialize task
    task_id = orchestrator.initialize_task(
        user_request="Perform reconnaissance on example.com",
        mode="offensive",
        target="example.com",
    )

    print(f"\nTask initialized: {task_id}")
    print(f"Status: {orchestrator.get_status()}")

    # Execute task
    results = orchestrator.execute_task()

    print(f"\nExecution results:")
    print(json.dumps(results, indent=2))
