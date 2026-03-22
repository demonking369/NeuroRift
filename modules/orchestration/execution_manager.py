import asyncio
import logging
import shlex
import subprocess
from datetime import datetime
from typing import Dict, Optional, List, Any
from pathlib import Path

from modules.orchestration.data_models import (
    ToolExecutionResult,
    ScanRequest,
    SessionContext,
)
from modules.tools.base import BaseTool, ToolMode
from modules.tools.wrappers.amass import AmassTool
from modules.tools.wrappers.masscan import MasscanTool
from modules.tools.wrappers.nmap import NmapTool
from modules.tools.wrappers.unicornscan import UnicornscanTool
from modules.tools.wrappers.ike_scan import IkeScanTool
from modules.tools.wrappers.sqlmap import SqlmapTool
from modules.tools.wrappers.metasploit import MetasploitTool
from modules.tools.wrappers.netcat import NetcatTool
from modules.tools.wrappers.mitmproxy import MitmproxyTool
from modules.tools.wrappers.wireshark import WiresharkTool


class ExecutionManager:
    def __init__(self, session_manager=None):
        self.logger = logging.getLogger(__name__)
        self.session_manager = session_manager
        self.tools: Dict[str, BaseTool] = self._register_tools()
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def _register_tools(self) -> Dict[str, BaseTool]:
        # Initialize all available tools
        tools = [
            AmassTool(),
            MasscanTool(),
            NmapTool(),
            UnicornscanTool(),
            IkeScanTool(),
            SqlmapTool(),
            MetasploitTool(),
            NetcatTool(),
            MitmproxyTool(),
            WiresharkTool(),
        ]
        return {t.name: t for t in tools}

    async def execute_tool(
        self, request: ScanRequest, context: SessionContext
    ) -> ToolExecutionResult:
        tool = self.tools.get(request.tool_name)
        if not tool:
            raise ValueError(f"Tool {request.tool_name} not found")

        # Mode Safety Check
        current_mode = request.mode_override or context.mode
        if tool.mode == ToolMode.OFFENSIVE and current_mode != ToolMode.OFFENSIVE:
            # Check if attempting to run offensive tool in defensive mode
            if hasattr(current_mode, "value"):
                if current_mode.value != "offensive":  # Strict check
                    raise PermissionError(
                        f"Cannot run offensive tool {tool.name} in {current_mode} mode"
                    )
            elif current_mode != "offensive":
                raise PermissionError(
                    f"Cannot run offensive tool {tool.name} in {current_mode} mode"
                )

        # Input Validation
        from modules.tools.base import ToolInput

        tool_input = ToolInput(target=request.target, args=request.args)
        if not tool.validate_input(tool_input):
            raise ValueError(f"Invalid input for tool {tool.name}")

        # Build Command
        cmd_list = tool.build_command(tool_input)
        cmd_str = shlex.join(cmd_list)

        self.logger.info(f"Executing: {cmd_str}")
        start_time = datetime.now()

        # Execute
        try:
            # Run asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd_list,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            end_time = datetime.now()

            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            full_output = stdout_str + "\n" + stderr_str

            # Parse Output
            structured = tool.parse_output(stdout_str)

            result = ToolExecutionResult(
                tool_name=tool.name,
                command=cmd_str,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                status="success" if process.returncode == 0 else "failed",
                raw_output=full_output,
                structured_output=structured,
            )

            # Log to session context
            context.history.append(result)
            return result

        except Exception as e:
            end_time = datetime.now()
            self.logger.error(f"Execution failed: {e}")
            return ToolExecutionResult(
                tool_name=tool.name,
                command=cmd_str,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds(),
                status="error",
                raw_output="",
                error=str(e),
            )

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "mode": t.mode.value,
                "installed": t.check_installed(),
            }
            for t in self.tools.values()
        ]
