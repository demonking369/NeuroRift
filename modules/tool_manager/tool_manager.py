#!/usr/bin/env python3
"""
NeuroRift Tool Manager Module
Manages installation and updates of security tools
"""

import os
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)


class ToolManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.logger = logging.getLogger(__name__)
        self.console = Console()
        self.tools_dir = self.base_dir / "tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)

        # Load tool configurations
        self.tools_config = self._load_tools_config()

    def _load_tools_config(self) -> Dict[str, Any]:
        """Load tool configurations from JSON"""
        config_path = self.base_dir / "config" / "tools.json"
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load tools config: {e}")
            return {}

    def install_tool(self, tool_name: str) -> Dict[str, Any]:
        """Install a security tool"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            # Check if tool exists in config
            if tool_name not in self.tools_config:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} not found in configuration",
                }

            tool_config = self.tools_config[tool_name]

            # Check if tool is already installed
            task = progress.add_task("Checking installation...", total=None)
            if self._is_tool_installed(tool_name):
                progress.update(task, completed=True)
                return {
                    "success": True,
                    "message": f"Tool {tool_name} is already installed",
                }

            # Create tool directory
            task = progress.add_task("Creating tool directory...", total=None)
            tool_dir = self.tools_dir / tool_name
            tool_dir.mkdir(exist_ok=True)
            progress.update(task, completed=True)

            # Download tool
            task = progress.add_task("Downloading tool...", total=None)
            try:
                download_path = self._download_tool(tool_name, tool_config)
                progress.update(task, completed=True)
            except Exception as e:
                self.logger.error(f"Failed to download tool {tool_name}: {e}")
                return {"success": False, "error": f"Failed to download tool: {str(e)}"}

            # Install tool
            task = progress.add_task("Installing tool...", total=None)
            try:
                self._install_tool_files(tool_name, download_path, tool_config)
                progress.update(task, completed=True)
            except Exception as e:
                self.logger.error(f"Failed to install tool {tool_name}: {e}")
                return {"success": False, "error": f"Failed to install tool: {str(e)}"}

            # Verify installation
            task = progress.add_task("Verifying installation...", total=None)
            if not self._verify_installation(tool_name, tool_config):
                progress.update(task, completed=True)
                return {
                    "success": False,
                    "error": f"Failed to verify tool installation",
                }
            progress.update(task, completed=True)

            return {"success": True, "message": f"Successfully installed {tool_name}"}

    def _is_tool_installed(self, tool_name: str) -> bool:
        """Check if a tool is installed"""
        tool_config = self.tools_config[tool_name]
        tool_dir = self.tools_dir / tool_name

        # Check if tool directory exists
        if not tool_dir.exists():
            return False

        # Check for required files
        for file in tool_config.get("required_files", []):
            if not (tool_dir / file).exists():
                return False

        # Check if tool is executable
        if tool_config.get("executable"):
            executable = tool_dir / tool_config["executable"]
            if not executable.exists() or not os.access(executable, os.X_OK):
                return False

        return True

    def _download_tool(self, tool_name: str, tool_config: Dict) -> Path:
        """Download tool files"""
        download_url = tool_config["download_url"]
        download_dir = self.tools_dir / tool_name / "downloads"
        download_dir.mkdir(exist_ok=True)

        # Download file
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # Get filename from URL
        filename = download_url.split("/")[-1]
        download_path = download_dir / filename

        # Save file
        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return download_path

    def _install_tool_files(
        self, tool_name: str, download_path: Path, tool_config: Dict
    ) -> None:
        """Install tool files"""
        tool_dir = self.tools_dir / tool_name

        # Extract archive if needed
        if download_path.suffix in [".zip", ".tar.gz", ".tgz"]:
            if download_path.suffix == ".zip":
                import zipfile

                with zipfile.ZipFile(download_path, "r") as zip_ref:
                    zip_ref.extractall(tool_dir)
            else:
                import tarfile

                with tarfile.open(download_path, "r:gz") as tar_ref:
                    tar_ref.extractall(tool_dir)

        # Copy files to tool directory
        for file in tool_config.get("files", []):
            src = tool_dir / file["source"]
            dst = tool_dir / file["destination"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        # Make executable if needed
        if tool_config.get("executable"):
            executable = tool_dir / tool_config["executable"]
            os.chmod(executable, 0o755)

    def _verify_installation(self, tool_name: str, tool_config: Dict) -> bool:
        """Verify tool installation"""
        tool_dir = self.tools_dir / tool_name

        # Check required files
        for file in tool_config.get("required_files", []):
            if not (tool_dir / file).exists():
                return False

        # Check executable
        if tool_config.get("executable"):
            executable = tool_dir / tool_config["executable"]
            if not executable.exists() or not os.access(executable, os.X_OK):
                return False

        # Run verification command if specified
        if tool_config.get("verify_command"):
            try:
                result = subprocess.run(
                    tool_config["verify_command"],
                    cwd=tool_dir,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    return False
            except Exception as e:
                self.logger.error(f"Failed to verify tool {tool_name}: {e}")
                return False

        return True

    def update_tool(self, tool_name: str) -> Dict[str, Any]:
        """Update an installed tool"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            # Check if tool exists in config
            if tool_name not in self.tools_config:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} not found in configuration",
                }

            # Check if tool is installed
            task = progress.add_task("Checking installation...", total=None)
            if not self._is_tool_installed(tool_name):
                progress.update(task, completed=True)
                return {"success": False, "error": f"Tool {tool_name} is not installed"}

            tool_config = self.tools_config[tool_name]

            # Backup current installation
            task = progress.add_task("Backing up current installation...", total=None)
            tool_dir = self.tools_dir / tool_name
            backup_dir = tool_dir.parent / f"{tool_name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(tool_dir, backup_dir)
            progress.update(task, completed=True)

            # Download new version
            task = progress.add_task("Downloading new version...", total=None)
            try:
                download_path = self._download_tool(tool_name, tool_config)
                progress.update(task, completed=True)
            except Exception as e:
                self.logger.error(f"Failed to download new version of {tool_name}: {e}")
                # Restore backup
                shutil.rmtree(tool_dir)
                shutil.copytree(backup_dir, tool_dir)
                return {
                    "success": False,
                    "error": f"Failed to download new version: {str(e)}",
                }

            # Install new version
            task = progress.add_task("Installing new version...", total=None)
            try:
                self._install_tool_files(tool_name, download_path, tool_config)
                progress.update(task, completed=True)
            except Exception as e:
                self.logger.error(f"Failed to install new version of {tool_name}: {e}")
                # Restore backup
                shutil.rmtree(tool_dir)
                shutil.copytree(backup_dir, tool_dir)
                return {
                    "success": False,
                    "error": f"Failed to install new version: {str(e)}",
                }

            # Verify new installation
            task = progress.add_task("Verifying new installation...", total=None)
            if not self._verify_installation(tool_name, tool_config):
                progress.update(task, completed=True)
                # Restore backup
                shutil.rmtree(tool_dir)
                shutil.copytree(backup_dir, tool_dir)
                return {"success": False, "error": f"Failed to verify new installation"}
            progress.update(task, completed=True)

            # Remove backup
            shutil.rmtree(backup_dir)

            return {"success": True, "message": f"Successfully updated {tool_name}"}

    def uninstall_tool(self, tool_name: str) -> Dict[str, Any]:
        """Uninstall a tool"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            # Check if tool exists in config
            if tool_name not in self.tools_config:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} not found in configuration",
                }

            # Check if tool is installed
            task = progress.add_task("Checking installation...", total=None)
            if not self._is_tool_installed(tool_name):
                progress.update(task, completed=True)
                return {"success": False, "error": f"Tool {tool_name} is not installed"}

            # Create backup
            task = progress.add_task("Creating backup...", total=None)
            tool_dir = self.tools_dir / tool_name
            backup_dir = tool_dir.parent / f"{tool_name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree(tool_dir, backup_dir)
            progress.update(task, completed=True)

            # Remove tool
            task = progress.add_task("Removing tool...", total=None)
            try:
                shutil.rmtree(tool_dir)
                progress.update(task, completed=True)
            except Exception as e:
                self.logger.error(f"Failed to remove tool {tool_name}: {e}")
                # Restore backup
                shutil.copytree(backup_dir, tool_dir)
                return {"success": False, "error": f"Failed to remove tool: {str(e)}"}

            # Remove backup
            shutil.rmtree(backup_dir)

            return {"success": True, "message": f"Successfully uninstalled {tool_name}"}

    def list_tools(self) -> Dict[str, Any]:
        """List installed tools"""
        tools = {}

        for tool_name, tool_config in self.tools_config.items():
            tools[tool_name] = {
                "installed": self._is_tool_installed(tool_name),
                "version": (
                    self._get_tool_version(tool_name)
                    if self._is_tool_installed(tool_name)
                    else None
                ),
                "description": tool_config.get("description", ""),
                "website": tool_config.get("website", ""),
                "repository": tool_config.get("repository", ""),
            }

        return {"success": True, "tools": tools}

    def _get_tool_version(self, tool_name: str) -> Optional[str]:
        """Get installed tool version"""
        tool_config = self.tools_config[tool_name]

        if tool_config.get("version_command"):
            try:
                result = subprocess.run(
                    tool_config["version_command"],
                    cwd=self.tools_dir / tool_name,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception as e:
                self.logger.error(f"Failed to get version for {tool_name}: {e}")

        return None
