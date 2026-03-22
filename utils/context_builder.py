#!/usr/bin/env python3
"""
NeuroRift Context Builder
Manages dynamic AI prompts with context from tools and previous results
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class ContextBuilder:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)
        self.context_history = []
        self.max_history = 10
        self.prompt_templates_dir = self.base_dir / "prompts"
        self.prompt_templates_dir.mkdir(parents=True, exist_ok=True)

    def add_tool_output(
        self, tool_name: str, output: str, metadata: Optional[Dict] = None
    ):
        """Add tool output to context history"""
        context = {
            "type": "tool_output",
            "tool": tool_name,
            "output": output,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._add_to_history(context)

    def add_ai_response(
        self, prompt: str, response: str, metadata: Optional[Dict] = None
    ):
        """Add AI response to context history"""
        context = {
            "type": "ai_response",
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._add_to_history(context)

    def add_scan_result(self, result_type: str, data: Dict):
        """Add scan result to context history"""
        context = {
            "type": "scan_result",
            "result_type": result_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self._add_to_history(context)

    def _add_to_history(self, context: Dict):
        """Add context to history with size limit"""
        self.context_history.append(context)
        if len(self.context_history) > self.max_history:
            self.context_history.pop(0)

    def build_prompt(self, template_name: str, variables: Dict) -> str:
        """Build prompt from template with context"""
        template = self._load_template(template_name)
        if not template:
            return ""

        # Add context to variables
        variables["context"] = self._format_context()

        # Replace variables in template
        prompt = template
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{ {key} }}}}", str(value))

        return prompt

    def _load_template(self, template_name: str) -> Optional[str]:
        """Load prompt template"""
        template_path = self.prompt_templates_dir / f"{template_name}.jinja"
        try:
            if template_path.exists():
                with open(template_path) as f:
                    return f.read()
            return None
        except Exception as e:
            self.logger.error(f"Error loading template {template_name}: {e}")
            return None

    def _format_context(self) -> str:
        """Format context history for prompt"""
        context_str = []

        for ctx in self.context_history:
            if ctx["type"] == "tool_output":
                context_str.append(f"Tool: {ctx['tool']}\nOutput: {ctx['output']}")
            elif ctx["type"] == "ai_response":
                context_str.append(f"Previous AI Response: {ctx['response']}")
            elif ctx["type"] == "scan_result":
                context_str.append(
                    f"Scan Result ({ctx['result_type']}): {json.dumps(ctx['data'])}"
                )

        return "\n\n".join(context_str)

    def save_template(self, template_name: str, content: str):
        """Save new prompt template"""
        template_path = self.prompt_templates_dir / f"{template_name}.jinja"
        try:
            with open(template_path, "w") as f:
                f.write(content)
        except Exception as e:
            self.logger.error(f"Error saving template {template_name}: {e}")

    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        return [f.stem for f in self.prompt_templates_dir.glob("*.jinja")]

    def clear_history(self):
        """Clear context history"""
        self.context_history.clear()

    def export_context(self, filepath: Path):
        """Export context history to file"""
        try:
            with open(filepath, "w") as f:
                json.dump(self.context_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error exporting context: {e}")

    def import_context(self, filepath: Path):
        """Import context history from file"""
        try:
            with open(filepath) as f:
                self.context_history = json.load(f)
        except Exception as e:
            self.logger.error(f"Error importing context: {e}")

    def get_relevant_context(self, query: str, max_items: int = 5) -> List[Dict]:
        """Get most relevant context items for a query"""
        # Simple relevance scoring based on keyword matching
        scored_items = []
        keywords = set(re.findall(r"\w+", query.lower()))

        for item in self.context_history:
            score = 0
            content = ""

            if item["type"] == "tool_output":
                content = f"{item['tool']} {item['output']}"
            elif item["type"] == "ai_response":
                content = f"{item['prompt']} {item['response']}"
            elif item["type"] == "scan_result":
                content = json.dumps(item["data"])

            content_words = set(re.findall(r"\w+", content.lower()))
            score = len(keywords.intersection(content_words))

            scored_items.append((score, item))

        # Sort by score and return top items
        scored_items.sort(reverse=True)
        return [item for _, item in scored_items[:max_items]]
