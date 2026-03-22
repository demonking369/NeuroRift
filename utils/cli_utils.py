"""
CLI utilities for NeuroRift
Handles banner display and results formatting
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import Dict, List, Any
import json
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def print_banner(version: str):
    """Print NeuroRift banner"""
    banner = f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    NeuroRift v{version}                       ║
    ║              Educational Security Framework                   ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def print_results_table(results: dict):
    """Print results in a formatted table"""
    for category, items in results.items():
        if not items:
            continue

        table = Table(title=f"{category} Results")
        table.add_column("Item", style="cyan")
        table.add_column("Details", style="green")

        for item in items:
            if isinstance(item, dict):
                details = ", ".join(f"{k}: {v}" for k, v in item.items())
            else:
                details = str(item)
            table.add_row(str(item), details)

        console.print(table)


def print_json_results(results: Dict[str, Any]):
    """Print results in JSON format"""
    console.print(json.dumps(results, indent=2))


def print_error(message: str):
    """Print error message"""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_success(message: str):
    """Print success message"""
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_info(message: str):
    """Print info message"""
    console.print(f"[bold blue]Info:[/bold blue] {message}")


def print_progress(message: str):
    """Print progress message"""
    console.print(f"[bold cyan]Progress:[/bold cyan] {message}")


def print_debug(message: str):
    """Print debug message"""
    console.print(f"[bold magenta]Debug:[/bold magenta] {message}")


def print_stealth_stats(stats: Dict[str, Any]):
    """Print stealth statistics"""
    table = Table(title="\nStealth Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in stats.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


def create_progress(description: str):
    """Create a progress bar"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )
