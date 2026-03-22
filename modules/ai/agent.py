import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from modules.ai.ai_integration import LocalAIClient


class NeuroRiftAgent:
    """Simple Agentic AI for NeuroRift.

    This agent understands the framework modules and outputs structured
    action intents in JSON format.
    """

    def __init__(self, llm_client: Optional[LocalAIClient] = None):
        self.llm_client = llm_client or LocalAIClient()
        self.logger = logging.getLogger("neurorift.agent")
        self.prompt_path = (
            Path(__file__).resolve().parents[2] / "prompts" / "agentic_system.md"
        )
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the agentic system prompt from file."""
        try:
            if self.prompt_path.exists():
                return self.prompt_path.read_text()
            else:
                self.logger.warning(f"System prompt not found at {self.prompt_path}")
                return "You are a security assistant for the NeuroRift framework."
        except Exception as e:
            self.logger.error(f"Error loading system prompt: {e}")
            return "You are a security assistant for the NeuroRift framework."

    async def run_task(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a user task and return a structured response.

        Args:
            task: The user's request or task description.
            context: Additional context like current module, available tools, etc.

        Returns:
            A dictionary containing the AI's plan or response.
        """
        # Prepare prompt
        prompt = f"User Task: {task}\n"
        if context:
            prompt += f"Context: {json.dumps(context, indent=2)}\n"

        prompt += "\nRespond with a JSON object. Follow the schema exactly.\n"

        self.logger.info(f"Agent processing task: {task[:50]}...")

        # Define the schema for llama.cpp to enforce
        schema = {
            "type": "object",
            "properties": {
                "thought": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": [
                        "ACTION_PLAN",
                        "ACTION_EXECUTION",
                        "RESPONSE",
                        "CLARIFICATION",
                    ],
                },
                "goal": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "ui_click",
                                    "ui_input",
                                    "module_call",
                                    "tool_call",
                                ],
                            },
                            "target": {
                                "type": "string",
                                "enum": [
                                    "recon_scan",
                                    "robin_search",
                                    "ai_assistant",
                                    "nmap",
                                    "subfinder",
                                    "httpx",
                                    "nuclei",
                                    "gobuster",
                                    "ffuf",
                                    "whatweb",
                                    "Overview",
                                    "Recon",
                                    "Robin",
                                    "Tool Manager",
                                    "Assistant",
                                    "Reports",
                                    "Settings",
                                    "domain_input",
                                    "query_input",
                                ],
                            },
                            "value": {"type": "string"},
                            "reason": {"type": "string"},
                        },
                        "required": ["type", "target", "value", "reason"],
                    },
                },
                "content": {"type": "string"},
            },
            "required": ["thought", "mode", "goal", "steps"],
        }

        # Pass schema to llama.cpp
        raw_response = self.llm_client.generate(
            prompt, system_prompt=self._system_prompt, format=schema
        )

        if not raw_response:
            return {
                "mode": "RESPONSE",
                "content": "I apologize, but I failed to generate a response. Please check the llama.cpp service.",
                "status": "error",
            }

        return self._parse_response(raw_response)

    def _parse_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse and validate the AI's response with enhanced JSON extraction."""
        try:
            # 1. Try finding a JSON block within triple backticks
            json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw_response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # 2. Try finding the first '{' and the last '}'
            first_brace = raw_response.find("{")
            last_brace = raw_response.rfind("}")
            if first_brace != -1 and last_brace != -1:
                json_candidate = raw_response[first_brace : last_brace + 1]
                try:
                    return json.loads(json_candidate)
                except json.JSONDecodeError:
                    pass

            # 3. If no JSON found, treat as plain response
            self.logger.debug(
                "No valid JSON found in AI response, falling back to RESPONSE mode."
            )
            return {
                "mode": "RESPONSE",
                "content": raw_response,
                "status": "partial_success",
                "parsing_error": "No valid JSON structure identified",
            }

        except Exception as e:
            self.logger.error(f"Unexpected error during parsing: {e}")
            return {
                "mode": "RESPONSE",
                "content": raw_response,
                "status": "error",
                "parsing_error": str(e),
            }

    def get_readiness_status(self) -> Dict[str, Any]:
        """Check if the agent is ready for operation."""
        is_llama_available = self.llm_client.is_available()
        best_model = self.llm_client.get_best_model() if is_llama_available else None

        return {
            "ready": is_llama_available and best_model is not None,
            "llama_available": is_llama_available,
            "model_ready": best_model is not None,
            "active_model": best_model,
        }
