#!/usr/bin/env python3
"""
NeuroRift Configuration Wizard
Interactive CLI for managing NeuroRift settings and environment variables.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from dotenv import load_dotenv, set_key

# Import LocalAIClient to check available models
from modules.ai.ai_integration import LocalAIClient
import asyncio


class ConfigWizard:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.env_path = base_dir / ".env"
        self.console = Console()
        self.llm_client = LocalAIClient()

        # Load existing env vars
        load_dotenv(self.env_path)

    def run(self):
        """Run the interactive configuration wizard"""
        self.console.clear()
        self.console.print(
            Panel(
                "[bold cyan]NeuroRift Configuration Wizard[/bold cyan]\n"
                "Configure your AI models, API keys, and system settings.",
                title="Setup",
                border_style="blue",
            )
        )

        while True:
            self.console.print("\n[bold]Main Menu[/bold]")
            self.console.print("1. [cyan]AI Configuration[/cyan] (Models & Provider)")
            self.console.print("2. [cyan]System Settings[/cyan] (Directories, Logging)")
            self.console.print("3. [cyan]View Current Config[/cyan]")
            self.console.print("4. [red]Exit[/red]")

            choice = Prompt.ask(
                "Select an option", choices=["1", "2", "3", "4"], default="4"
            )

            if choice == "1":
                asyncio.run(self.configure_ai())
            elif choice == "2":
                self.configure_system()
            elif choice == "3":
                self.show_current_config()
            elif choice == "4":
                self.console.print("[green]Configuration saved. Exiting...[/green]")
                break

    async def configure_ai(self):
        """Configure AI settings"""
        self.console.print("\n[bold blue]AI Configuration[/bold blue]")

        # Check current settings
        current_main = os.getenv("LLAMA_MAIN_MODEL", "Not Set")
        current_assistant = os.getenv("LLAMA_ASSISTANT_MODEL", "Not Set")

        self.console.print(f"Current Main Model: [green]{current_main}[/green]")
        self.console.print(
            f"Current Assistant Model: [green]{current_assistant}[/green]"
        )

        if Confirm.ask("Do you want to change AI models?"):
            # List available models
            self.console.print("Fetching available models from llama.cpp...")
            if not await self.llm_client.ensure_service_running():
                self.console.print(
                    "[red]Could not connect to llama.cpp. Is it installed?[/red]"
                )
                return

            models = await self.llm_client.list_models()
            if not models:
                self.console.print("[yellow]No models found in llama.cpp.[/yellow]")
                return

            model_names = [m["name"] for m in models]

            # Display models
            table = Table(title="Available llama.cpp Models")
            table.add_column("Index", justify="right", style="cyan")
            table.add_column("Model Name", style="white")

            for idx, name in enumerate(model_names):
                table.add_row(str(idx + 1), name)

            self.console.print(table)

            # Select Main Model
            main_idx = Prompt.ask(
                "Select Main Model (number)",
                choices=[str(i + 1) for i in range(len(model_names))],
            )
            selected_main = model_names[int(main_idx) - 1]
            self.update_env("LLAMA_MAIN_MODEL", selected_main)

            # Select Assistant Model
            asst_idx = Prompt.ask(
                "Select Assistant Model (number)",
                choices=[str(i + 1) for i in range(len(model_names))],
                default=main_idx,
            )
            selected_asst = model_names[int(asst_idx) - 1]
            self.update_env("LLAMA_ASSISTANT_MODEL", selected_asst)

            self.console.print("[green]AI Models updated successfully![/green]")

    def configure_system(self):
        """Configure system settings"""
        self.console.print("\n[bold blue]System Settings[/bold blue]")

        # Log Level
        current_log = os.getenv("LOG_LEVEL", "INFO")
        new_log = Prompt.ask(
            "Log Level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default=current_log,
        )
        self.update_env("LOG_LEVEL", new_log)

        self.console.print("[green]System settings updated![/green]")

    def show_current_config(self):
        """Display current configuration"""
        table = Table(title="Current Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")

        config_keys = [
            "LLAMA_MAIN_MODEL",
            "LLAMA_ASSISTANT_MODEL",
            "LOG_LEVEL",
            "NEURORIFT_HOME",
            "AI_ENABLED",
        ]

        for key in config_keys:
            table.add_row(key, os.getenv(key, "Not Set"))

        self.console.print(table)
        Prompt.ask("Press Enter to continue")

    def update_env(self, key: str, value: str):
        """Update .env file and current environment"""
        # Create .env if it doesn't exist
        if not self.env_path.exists():
            self.env_path.touch()

        set_key(self.env_path, key, value)
        os.environ[key] = value
        self.console.print(f"[dim]Updated {key} = {value}[/dim]")


if __name__ == "__main__":
    wizard = ConfigWizard(Path.cwd())
    wizard.run()
