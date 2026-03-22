#!/usr/bin/env python3
"""
Configuration Manager for NeuroRift
Handles loading and managing configuration settings
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    def __init__(self, config_path: str):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config_dir = self.config_path.parent / "configs"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            self.logger.warning("Config file not found: %s", self.config_path)
            # If config file doesn't exist, save a default one and then load it
            default_config = self._get_default_config()
            self.config = (
                default_config  # Temporarily set to default for _save_config to work
            )
            self._save_config()
            return default_config  # Return the default config
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            self.logger.error("Error loading config: %s", e)
            # Return default config on error
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "ai": {
                "preferred_model": "deepseek-coder-v2:16b-lite-base-q4_0",
                "assistant_model": "mistral:7b-instruct-v0.2-q4_0",
                "base_url": "http://localhost:8080",
                "timeout": 300,
                "max_tokens": 4096,
            },
            "scanning": {"max_threads": 10, "timeout": 300},
            "stealth": {"enabled": False, "min_delay": 1, "max_delay": 5},
            "reporting": {"default_format": "all"},
            "tools": {
                "subfinder": {"enabled": True},
                "httpx": {"enabled": True},
                "nuclei": {"enabled": True},
                "nmap": {"enabled": True},
            },
            "notifications": {
                "email": {"enabled": False},
                "discord": {"enabled": False},
                "slack": {"enabled": False},
                "webhook": {"enabled": False},
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
        self._save_config()

    def _save_config(self) -> None:
        """Save configuration to file"""
        try:
            # SECURITY FIX: Set secure file permissions (0o600) for sensitive config files
            # This ensures only the owner can read/write the file
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            os.chmod(self.config_path, 0o600)
        except Exception as e:
            self.logger.error("Error saving config: %s", e)

    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration"""
        return self.config.get("ai", {})

    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return self.config.get("notifications", {})

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """Get tool-specific configuration"""
        return self.config.get("tools", {}).get(tool_name, {})

    def save_config(self):
        """Save current configuration to file"""
        try:
            # SECURITY FIX: Set secure file permissions for sensitive config files
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            os.chmod(self.config_path, 0o600)
        except Exception as e:
            self.logger.error("Error saving config: %s", e)

    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        self.config = {**self.config, **updates}
        self._save_config()

    def reset(self):
        """Reset configuration to defaults"""
        self.config = self._load_config()
        self._save_config()

    def export(self, filepath: Path):
        """Export configuration to file"""
        try:
            # SECURITY FIX: Set secure file permissions for exported config files
            with open(filepath, "w") as f:
                json.dump(self.config, f, indent=2)
            os.chmod(filepath, 0o600)
        except Exception as e:
            self.logger.error("Error exporting config: %s", e)

    def import_config(self, filepath: Path):
        """Import configuration from file"""
        try:
            with open(filepath) as f:
                imported_config = json.load(f)
                self.config = {**self.config, **imported_config}
                self._save_config()
        except Exception as e:
            self.logger.error("Error importing config: %s", e)

    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self.config.copy()

    def validate(self) -> bool:
        """Validate configuration"""
        required_keys = [
            "ai.preferred_model",
            "scanning.max_threads",
            "stealth.enabled",
            "reporting.default_format",
        ]

        for key in required_keys:
            if self.get(key) is None:
                self.logger.error("Missing required config key: %s", key)
                return False

        return True
