import shutil
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class MetasploitTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="metasploit",
            description="Penetration testing framework",
            category=ToolCategory.EXPLOITATION,
            mode=ToolMode.DEFENSIVE,
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        # Metasploit needs at least a command or resource script
        return bool(
            input_data.args.get("resource_script") or input_data.args.get("command")
        )

    def build_command(self, input_data: ToolInput) -> List[str]:
        cmd = ["msfconsole", "-q"]  # Quiet mode

        resource = input_data.args.get("resource_script")
        if resource:
            cmd.extend(["-r", resource])

        command = input_data.args.get("command")
        if command:
            cmd.extend(["-x", command])

        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # Metasploit output is very unstructured unless using specific plugins.
        # Check for success indicators.
        success = (
            "Meterpreter session" in raw_output or "Command shell session" in raw_output
        )
        return {
            "success_indicator": success,
            "raw_output": raw_output,  # Return full output for AI analysis
        }

    def check_installed(self) -> bool:
        return shutil.which("msfconsole") is not None
