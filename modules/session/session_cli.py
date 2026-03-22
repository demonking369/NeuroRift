#!/usr/bin/env python3
"""
NeuroRift Session CLI
Command-line interface for session management.

Designed and developed by demonking369
"""

import sys
import argparse
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from pathlib import Path
from typing import Optional

from modules.session import SessionManager, SessionStatus


class SessionCLI:
    """
    CLI interface for NeuroRift session management.

    Commands:
    - session new
    - session save
    - session list
    - session load <id>
    - session resume [id]
    - session delete <id>
    - session rename <id> <name>
    - session status
    - session export <id> <path>
    """

    def __init__(self, session_manager: Optional[SessionManager] = None):
        self.session_manager = session_manager or SessionManager()
        self.console = Console()
        self.logger = logging.getLogger(__name__)

    def cmd_new(self, args):
        """Create new session"""
        # Prompt for name if not provided
        if not args.name:
            name = Prompt.ask("Session name", default=f"Session {args.mode}")
        else:
            name = args.name

        # Create session
        session_id = self.session_manager.create_session(
            name=name, mode=args.mode, description=args.description or ""
        )

        self.console.print(
            f"\n[bold green]✓ Created session:[/bold green] {session_id}"
        )
        self.console.print(f"[cyan]Name:[/cyan] {name}")
        self.console.print(f"[cyan]Mode:[/cyan] {args.mode}")

        return session_id

    def cmd_save(self, args):
        """Save current session"""
        if not self.session_manager.current_session_id:
            self.console.print("[bold red]✗ No active session to save[/bold red]")
            return

        notes = args.notes or ""
        self.session_manager.save_session(notes=notes)

        self.console.print(
            f"\n[bold green]✓ Session saved:[/bold green] {self.session_manager.current_session_id}"
        )
        if notes:
            self.console.print(f"[cyan]Notes:[/cyan] {notes}")

    def cmd_list(self, args):
        """List all sessions"""
        sessions = self.session_manager.list_sessions(
            status=args.status, mode=args.mode
        )

        if not sessions:
            self.console.print("[yellow]No sessions found[/yellow]")
            return

        # Create table
        table = Table(title=f"NeuroRift Sessions ({len(sessions)})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Status", style="magenta")
        table.add_column("Mode", style="blue")
        table.add_column("Created", style="yellow")

        for session in sessions:
            # Truncate ID for display
            short_id = session["id"][-12:]

            # Format status with emoji
            status_emoji = {
                "active": "🟢",
                "paused": "⏸️ ",
                "completed": "✅",
                "failed": "❌",
            }
            status_display = (
                f"{status_emoji.get(session['status'], '')} {session['status']}"
            )

            table.add_row(
                short_id,
                session["name"],
                status_display,
                session["mode"],
                session.get("created_at", "N/A")[:10],
            )

        self.console.print(table)

    def cmd_load(self, args):
        """Load a session"""
        try:
            session_data = self.session_manager.load_session(args.session_id)

            self.console.print(
                f"\n[bold green]✓ Loaded session:[/bold green] {args.session_id}"
            )
            self.console.print(f"[cyan]Name:[/cyan] {session_data['session']['name']}")
            self.console.print(
                f"[cyan]Status:[/cyan] {session_data['session']['status']}"
            )
            self.console.print(f"[cyan]Mode:[/cyan] {session_data['session']['mode']}")

        except FileNotFoundError:
            self.console.print(
                f"[bold red]✗ Session not found:[/bold red] {args.session_id}"
            )

    def cmd_resume(self, args):
        """Resume a paused session"""
        try:
            session_data = self.session_manager.resume_session(args.session_id)

            self.console.print(
                f"\n[bold green]✓ Resumed session:[/bold green] {session_data['session']['id']}"
            )
            self.console.print(f"[cyan]Name:[/cyan] {session_data['session']['name']}")
            self.console.print(f"[cyan]Mode:[/cyan] {session_data['session']['mode']}")

            # Show progress if available
            progress = session_data.get("task_state", {}).get("progress", {})
            if progress.get("total_steps", 0) > 0:
                percentage = progress.get("percentage", 0)
                self.console.print(
                    f"[cyan]Progress:[/cyan] {percentage}% ({progress['completed_steps']}/{progress['total_steps']} steps)"
                )

        except ValueError as e:
            self.console.print(f"[bold red]✗ Error:[/bold red] {e}")
        except FileNotFoundError:
            self.console.print(f"[bold red]✗ Session not found[/bold red]")

    def cmd_delete(self, args):
        """Delete a session"""
        # Confirm deletion unless --force
        if not args.force:
            if not Confirm.ask(f"Delete session {args.session_id}?"):
                self.console.print("[yellow]Cancelled[/yellow]")
                return

        try:
            self.session_manager.delete_session(args.session_id, force=args.force)
            self.console.print(
                f"\n[bold green]✓ Deleted session:[/bold green] {args.session_id}"
            )
        except Exception as e:
            self.console.print(f"[bold red]✗ Error:[/bold red] {e}")

    def cmd_rename(self, args):
        """Rename a session"""
        try:
            self.session_manager.rename_session(args.session_id, args.new_name)
            self.console.print(
                f"\n[bold green]✓ Renamed session:[/bold green] {args.session_id}"
            )
            self.console.print(f"[cyan]New name:[/cyan] {args.new_name}")
        except Exception as e:
            self.console.print(f"[bold red]✗ Error:[/bold red] {e}")

    def cmd_status(self, args):
        """Show current session status"""
        if not self.session_manager.current_session_id:
            self.console.print("[yellow]No active session[/yellow]")
            return

        session_data = self.session_manager.get_current_session()
        if not session_data:
            self.console.print("[yellow]No session data loaded[/yellow]")
            return

        # Create status panel
        session_info = session_data["session"]
        task_state = session_data.get("task_state", {})
        progress = task_state.get("progress", {})

        status_text = f"""
[bold]Session ID:[/bold] {session_info['id']}
[bold]Name:[/bold] {session_info['name']}
[bold]Status:[/bold] {session_info['status']}
[bold]Mode:[/bold] {session_info['mode']}
[bold]Created:[/bold] {session_info['created_at']}
[bold]Updated:[/bold] {session_info['updated_at']}

[bold]Task:[/bold] {task_state.get('task_type', 'None')}
[bold]Target:[/bold] {task_state.get('target', 'None')}
[bold]Progress:[/bold] {progress.get('percentage', 0)}% ({progress.get('completed_steps', 0)}/{progress.get('total_steps', 0)} steps)
        """

        panel = Panel(status_text, title="Current Session", border_style="cyan")
        self.console.print(panel)

    def cmd_export(self, args):
        """Export a session"""
        try:
            from modules.session.session_serializer import SessionSerializer

            serializer = SessionSerializer()
            session_data = self.session_manager.load_session(args.session_id)

            export_path = Path(args.path).expanduser()
            serializer.export_session(
                session_data, export_path, include_data=args.include_data
            )

            self.console.print(
                f"\n[bold green]✓ Exported session:[/bold green] {args.session_id}"
            )
            self.console.print(f"[cyan]Export path:[/cyan] {export_path}")

        except Exception as e:
            self.console.print(f"[bold red]✗ Error:[/bold red] {e}")


def setup_session_parser(subparsers):
    """
    Setup session command parser.

    Args:
        subparsers: Argparse subparsers object
    """
    session_parser = subparsers.add_parser(
        "session", help="Session management commands"
    )
    session_subparsers = session_parser.add_subparsers(
        dest="session_command", help="Session commands"
    )

    # session new
    new_parser = session_subparsers.add_parser("new", help="Create new session")
    new_parser.add_argument("--name", help="Session name")
    new_parser.add_argument(
        "--mode",
        choices=["offensive", "defensive"],
        default="offensive",
        help="Operational mode",
    )
    new_parser.add_argument("--description", help="Session description")

    # session save
    save_parser = session_subparsers.add_parser("save", help="Save current session")
    save_parser.add_argument("--notes", help="Session notes")

    # session list
    list_parser = session_subparsers.add_parser("list", help="List all sessions")
    list_parser.add_argument(
        "--status", choices=["active", "paused", "completed"], help="Filter by status"
    )
    list_parser.add_argument(
        "--mode", choices=["offensive", "defensive"], help="Filter by mode"
    )

    # session load
    load_parser = session_subparsers.add_parser("load", help="Load a session")
    load_parser.add_argument("session_id", help="Session ID to load")

    # session resume
    resume_parser = session_subparsers.add_parser(
        "resume", help="Resume a paused session"
    )
    resume_parser.add_argument(
        "session_id", nargs="?", help="Session ID (uses last active if not provided)"
    )

    # session delete
    delete_parser = session_subparsers.add_parser("delete", help="Delete a session")
    delete_parser.add_argument("session_id", help="Session ID to delete")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # session rename
    rename_parser = session_subparsers.add_parser("rename", help="Rename a session")
    rename_parser.add_argument("session_id", help="Session ID to rename")
    rename_parser.add_argument("new_name", help="New session name")

    # session status
    status_parser = session_subparsers.add_parser(
        "status", help="Show current session status"
    )

    # session export
    export_parser = session_subparsers.add_parser("export", help="Export a session")
    export_parser.add_argument("session_id", help="Session ID to export")
    export_parser.add_argument("path", help="Export path")
    export_parser.add_argument(
        "--include-data", action="store_true", help="Include session data directory"
    )


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create parser
    parser = argparse.ArgumentParser(description="NeuroRift Session CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup session commands
    setup_session_parser(subparsers)

    # Parse args
    args = parser.parse_args()

    if args.command != "session":
        parser.print_help()
        sys.exit(1)

    # Initialize CLI
    cli = SessionCLI()

    # Execute command
    if args.session_command == "new":
        cli.cmd_new(args)
    elif args.session_command == "save":
        cli.cmd_save(args)
    elif args.session_command == "list":
        cli.cmd_list(args)
    elif args.session_command == "load":
        cli.cmd_load(args)
    elif args.session_command == "resume":
        cli.cmd_resume(args)
    elif args.session_command == "delete":
        cli.cmd_delete(args)
    elif args.session_command == "rename":
        cli.cmd_rename(args)
    elif args.session_command == "status":
        cli.cmd_status(args)
    elif args.session_command == "export":
        cli.cmd_export(args)
    else:
        parser.print_help()
