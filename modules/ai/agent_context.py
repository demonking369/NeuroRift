#!/usr/bin/env python3
"""
NeuroRift Agent Context
Manages agent-specific context and inter-agent communication.

Contributors:
- NeuroRift Core Team
- x1xhlol (system-prompts-and-models-of-ai-tools)
- SimStudioAI (conceptual orchestration)
- Anti-Gravity AI
"""

import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime


class AgentContext:
    """
    Manages context for agents in the NeuroRift orchestration system.

    Handles context handoffs between agents and maintains shared knowledge base.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.shared_knowledge: Dict[str, Any] = {}
        self.task_id: Optional[str] = None

        self.logger.info("Agent context manager initialized")

    def initialize(self, task_id: str, initial_context: Dict[str, Any]) -> None:
        """
        Initialize context for a new task.

        Args:
            task_id: Task identifier
            initial_context: Initial context data
        """
        self.task_id = task_id
        self.shared_knowledge = {
            "task_id": task_id,
            "initialized_at": datetime.now().isoformat(),
            **initial_context,
        }
        self.contexts = {}

        self.logger.info(f"Context initialized for task: {task_id}")

    def set_context(self, agent_name: str, context_data: Dict[str, Any]) -> None:
        """
        Set context for a specific agent.

        Args:
            agent_name: Name of the agent
            context_data: Context data to store
        """
        self.contexts[agent_name] = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "data": context_data,
        }

        self.logger.debug(f"Context set for agent: {agent_name}")

    def get_context(self, agent_name: str) -> Dict[str, Any]:
        """
        Get context for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent context data
        """
        agent_context = self.contexts.get(agent_name, {})
        return agent_context.get("data", {})

    def get_all_contexts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all agent contexts.

        Returns:
            Dictionary of all agent contexts
        """
        return self.contexts.copy()

    def update_shared_knowledge(self, key: str, value: Any) -> None:
        """
        Update shared knowledge base.

        Args:
            key: Knowledge key
            value: Knowledge value
        """
        self.shared_knowledge[key] = value
        self.logger.debug(f"Shared knowledge updated: {key}")

    def get_shared_knowledge(self, key: Optional[str] = None) -> Any:
        """
        Get shared knowledge.

        Args:
            key: Optional specific key to retrieve

        Returns:
            Knowledge value or entire knowledge base
        """
        if key:
            return self.shared_knowledge.get(key)
        return self.shared_knowledge.copy()

    def handoff_context(
        self, from_agent: str, to_agent: str, handoff_data: Optional[Dict] = None
    ) -> None:
        """
        Perform context handoff between agents.

        Args:
            from_agent: Source agent name
            to_agent: Destination agent name
            handoff_data: Optional additional handoff data
        """
        # Get source agent context
        source_context = self.get_context(from_agent)

        # Create handoff package
        handoff = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now().isoformat(),
            "source_context": source_context,
            "handoff_data": handoff_data or {},
            "shared_knowledge": self.shared_knowledge.copy(),
        }

        # Store handoff in destination agent context
        self.set_context(f"{to_agent}_handoff", handoff)

        self.logger.info(f"Context handoff: {from_agent} → {to_agent}")

    async def prune_context(self, max_size_mb: float = 10.0) -> None:
        """
        Prune context to stay within size limits using LLM recursive summarization.

        Args:
            max_size_mb: Maximum context size in megabytes
        """
        # Calculate current size
        context_json = json.dumps(self.contexts)
        current_size_mb = len(context_json.encode("utf-8")) / (1024 * 1024)

        if current_size_mb > max_size_mb:
            self.logger.warning(
                f"Context size ({current_size_mb:.2f}MB) exceeds limit ({max_size_mb}MB)"
            )

            # Remove oldest contexts
            sorted_contexts = sorted(
                self.contexts.items(), key=lambda x: x[1].get("timestamp", "")
            )

            from modules.ai.ai_integration import LocalAIClient

            llm_client = LocalAIClient()
            current_summary = self.shared_knowledge.get("historical_summary", "")

            while current_size_mb > max_size_mb and sorted_contexts:
                oldest_key, oldest_val = sorted_contexts.pop(0)

                # Context summarization via LLM instead of pure deletion (Manus context persistence strategy)
                prompt = f"Summarize the following agent execution context precisely, keeping only the hard data and facts:\\n{json.dumps(oldest_val)}"
                try:
                    summary = await llm_client.generate(
                        prompt,
                        system_prompt="You are a data compressor. Extract all actionable IPs, domains, and vulnerabilities concisely out of large text dumps. Omit pleasantries.",
                    )
                    if summary:
                        current_summary += f"\\n[{oldest_key} SUMMARY]: {summary}"
                except Exception as e:
                    self.logger.error(f"Summarization of {oldest_key} failed: {e}")

                del self.contexts[oldest_key]

                context_json = json.dumps(self.contexts)
                current_size_mb = len(context_json.encode("utf-8")) / (1024 * 1024)

                self.logger.info(f"Summarized and pruned context: {oldest_key}")

            self.shared_knowledge["historical_summary"] = current_summary

    def export_context(self) -> Dict[str, Any]:
        """
        Export all context data.

        Returns:
            Complete context export
        """
        return {
            "task_id": self.task_id,
            "shared_knowledge": self.shared_knowledge,
            "agent_contexts": self.contexts,
            "exported_at": datetime.now().isoformat(),
        }

    def import_context(self, context_data: Dict[str, Any]) -> None:
        """
        Import context data.

        Args:
            context_data: Context data to import
        """
        self.task_id = context_data.get("task_id")
        self.shared_knowledge = context_data.get("shared_knowledge", {})
        self.contexts = context_data.get("agent_contexts", {})

        self.logger.info(f"Context imported for task: {self.task_id}")

    def clear(self) -> None:
        """Clear all context data"""
        self.contexts = {}
        self.shared_knowledge = {}
        self.task_id = None
        self.logger.info("Context cleared")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize agent context
    context = AgentContext()

    # Initialize for a task
    context.initialize(
        "task_001",
        {
            "user_request": "Scan example.com",
            "mode": "offensive",
            "target": "example.com",
        },
    )

    # Set context for Planner
    context.set_context(
        "planner",
        {"plan_id": "plan_001", "steps": [{"step_id": 1, "tool": "subfinder"}]},
    )

    # Handoff to Operator
    context.handoff_context("planner", "operator")

    # Get Operator's handoff
    operator_handoff = context.get_context("operator_handoff")
    print(f"\nOperator received handoff from: {operator_handoff.get('from_agent')}")

    # Export context
    export = context.export_context()
    print(f"\nContext export size: {len(json.dumps(export))} bytes")
