import shutil
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class NetcatTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="netcat",
            description="Networking utility for reading/writing to network connections",
            category=ToolCategory.EXPLOITATION,  # Can be used for shells, but also recon
            mode=ToolMode.DEFENSIVE,
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        return bool(input_data.target) and bool(input_data.args.get("port"))

    def build_command(self, input_data: ToolInput) -> List[str]:
        cmd = ["nc"]

        if input_data.args.get("verbose"):
            cmd.append("-v")
        if input_data.args.get("udp"):
            cmd.append("-u")
        if input_data.args.get("zero_io"):  # Scanning mode
            cmd.append("-z")

        cmd.append(input_data.target)
        cmd.append(str(input_data.args.get("port")))
        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # Parse connection success
        # "Connection to 127.0.0.1 80 port [tcp/http] succeeded!"
        succeeded = "succeeded" in raw_output
        return {"connected": succeeded, "output": raw_output}

    def check_installed(self) -> bool:
        return shutil.which("nc") is not None or shutil.which("netcat") is not None
