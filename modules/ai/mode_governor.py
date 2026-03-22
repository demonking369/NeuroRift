#!/usr/bin/env python3
"""
NeuroRift Mode Governor
Enforces strict separation between OFFENSIVE and DEFENSIVE modes.

Contributors:
- NeuroRift Core Team
- x1xhlol (system-prompts-and-models-of-ai-tools)
- SimStudioAI (conceptual orchestration)
- Anti-Gravity AI
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime


class OperationalMode(Enum):
    """Operational modes for NeuroRift"""

    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"


class ModeViolation(Exception):
    """Raised when a mode violation is detected"""

    pass


class ModeGovernor:
    """
    Mode Governor enforces operational discipline between OFFENSIVE and DEFENSIVE modes.

    CRITICAL RULES:
    1. No cross-mode contamination
    2. Tool/module access strictly controlled per mode
    3. All violations logged
    4. Mode switching disabled by default
    """

    def __init__(self, config_path: str = "configs/neurorift_x_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_mode: Optional[OperationalMode] = None
        self.logger = logging.getLogger(__name__)
        self.violation_log: List[Dict] = []

        # Initialize mode governor
        self.enabled = self.config.get("mode_governor", {}).get("enabled", True)
        self.allow_mode_switching = self.config.get("mode_governor", {}).get(
            "allow_mode_switching", False
        )
        self.log_violations = self.config.get("mode_governor", {}).get(
            "log_violations", True
        )

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

    def set_mode(self, mode: str) -> None:
        """
        Set the operational mode.

        Args:
            mode: Either 'offensive' or 'defensive'

        Raises:
            ValueError: If mode is invalid
            ModeViolation: If mode switching is not allowed
        """
        try:
            new_mode = OperationalMode(mode.lower())
        except ValueError:
            raise ValueError(
                f"Invalid mode: {mode}. Must be 'offensive' or 'defensive'"
            )

        # Check if mode switching is allowed
        if self.current_mode is not None and self.current_mode != new_mode:
            if not self.allow_mode_switching:
                raise ModeViolation(
                    f"Mode switching is disabled. Cannot switch from {self.current_mode.value} to {new_mode.value}"
                )
            self.logger.warning(
                f"Mode switched from {self.current_mode.value} to {new_mode.value}"
            )

        self.current_mode = new_mode
        self.logger.info(f"Operational mode set to: {self.current_mode.value.upper()}")

    def get_allowed_tools(self) -> List[str]:
        """Get list of tools allowed in current mode"""
        if not self.current_mode:
            raise ModeViolation("No operational mode set")

        modes_config = self.config.get("mode_governor", {}).get("modes", {})
        mode_config = modes_config.get(self.current_mode.value, {})
        return mode_config.get("allowed_tools", [])

    def get_allowed_modules(self) -> List[str]:
        """Get list of modules allowed in current mode"""
        if not self.current_mode:
            raise ModeViolation("No operational mode set")

        modes_config = self.config.get("mode_governor", {}).get("modes", {})
        mode_config = modes_config.get(self.current_mode.value, {})
        return mode_config.get("allowed_modules", [])

    def get_restrictions(self) -> List[str]:
        """Get list of restrictions for current mode"""
        if not self.current_mode:
            raise ModeViolation("No operational mode set")

        modes_config = self.config.get("mode_governor", {}).get("modes", {})
        mode_config = modes_config.get(self.current_mode.value, {})
        return mode_config.get("restrictions", [])

    def validate_tool(self, tool_name: str) -> bool:
        """
        Validate if a tool is allowed in current mode.

        Args:
            tool_name: Name of the tool to validate

        Returns:
            True if tool is allowed, False otherwise

        Raises:
            ModeViolation: If tool is not allowed and violations are enforced
        """
        if not self.enabled:
            return True

        if not self.current_mode:
            raise ModeViolation("No operational mode set")

        allowed_tools = self.get_allowed_tools()

        if tool_name not in allowed_tools:
            violation = {
                "timestamp": datetime.now().isoformat(),
                "mode": self.current_mode.value,
                "violation_type": "unauthorized_tool",
                "tool": tool_name,
                "allowed_tools": allowed_tools,
            }

            if self.log_violations:
                self.violation_log.append(violation)
                self.logger.warning(
                    f"Tool violation: {tool_name} not allowed in {self.current_mode.value} mode"
                )

            raise ModeViolation(
                f"Tool '{tool_name}' is not allowed in {self.current_mode.value.upper()} mode. "
                f"Allowed tools: {', '.join(allowed_tools)}"
            )

        return True

    def validate_module(self, module_name: str) -> bool:
        """
        Validate if a module is allowed in current mode.

        Args:
            module_name: Name of the module to validate

        Returns:
            True if module is allowed, False otherwise

        Raises:
            ModeViolation: If module is not allowed and violations are enforced
        """
        if not self.enabled:
            return True

        if not self.current_mode:
            raise ModeViolation("No operational mode set")

        allowed_modules = self.get_allowed_modules()

        if module_name not in allowed_modules:
            violation = {
                "timestamp": datetime.now().isoformat(),
                "mode": self.current_mode.value,
                "violation_type": "unauthorized_module",
                "module": module_name,
                "allowed_modules": allowed_modules,
            }

            if self.log_violations:
                self.violation_log.append(violation)
                self.logger.warning(
                    f"Module violation: {module_name} not allowed in {self.current_mode.value} mode"
                )

            raise ModeViolation(
                f"Module '{module_name}' is not allowed in {self.current_mode.value.upper()} mode. "
                f"Allowed modules: {', '.join(allowed_modules)}"
            )

        return True

    def get_mode_prompt_file(self) -> Optional[str]:
        """Get the prompt file for current mode"""
        if not self.current_mode:
            return None

        modes_config = self.config.get("mode_governor", {}).get("modes", {})
        mode_config = modes_config.get(self.current_mode.value, {})
        return mode_config.get("prompt_file")

    def get_violation_log(self) -> List[Dict]:
        """Get the violation log"""
        return self.violation_log

    def save_violation_log(self, output_path: str) -> None:
        """Save violation log to file"""
        try:
            with open(output_path, "w") as f:
                json.dump(self.violation_log, f, indent=2)
            self.logger.info(f"Violation log saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save violation log: {e}")

    def get_mode_description(self) -> str:
        """Get description of current mode"""
        if not self.current_mode:
            return "No mode set"

        modes_config = self.config.get("mode_governor", {}).get("modes", {})
        mode_config = modes_config.get(self.current_mode.value, {})
        return mode_config.get("description", "No description available")

    def __repr__(self) -> str:
        mode_str = self.current_mode.value.upper() if self.current_mode else "NONE"
        return f"<ModeGovernor mode={mode_str} enabled={self.enabled}>"


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize Mode Governor
    governor = ModeGovernor()

    # Set OFFENSIVE mode
    print("\n=== Testing OFFENSIVE Mode ===")
    governor.set_mode("offensive")
    print(f"Current mode: {governor.current_mode.value}")
    print(f"Description: {governor.get_mode_description()}")
    print(f"Allowed tools: {governor.get_allowed_tools()}")
    print(f"Restrictions: {governor.get_restrictions()}")

    # Test valid tool
    try:
        governor.validate_tool("nmap")
        print("✓ nmap is allowed in OFFENSIVE mode")
    except ModeViolation as e:
        print(f"✗ {e}")

    # Test invalid tool
    try:
        governor.validate_tool("patch_validator")
        print("✓ patch_validator is allowed in OFFENSIVE mode")
    except ModeViolation as e:
        print(f"✗ {e}")

    # Set DEFENSIVE mode (will fail if mode switching disabled)
    print("\n=== Testing DEFENSIVE Mode ===")
    try:
        governor.set_mode("defensive")
        print(f"Current mode: {governor.current_mode.value}")
        print(f"Allowed modules: {governor.get_allowed_modules()}")
    except ModeViolation as e:
        print(f"✗ Mode switching failed: {e}")
