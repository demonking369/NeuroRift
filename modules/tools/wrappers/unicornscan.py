import shutil
import re
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class UnicornscanTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="unicornscan",
            description="Asynchronous TCP/UDP port scanner",
            category=ToolCategory.RECON,
            mode=ToolMode.OFFENSIVE,
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        return bool(input_data.target)

    def build_command(self, input_data: ToolInput) -> List[str]:
        cmd = ["unicornscan", input_data.target]
        ports = input_data.args.get("ports")
        if ports:
            cmd.extend(["-p", ports])
        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # Example: TCP open 192.168.1.1:80  ttl 128
        findings = []
        # Regex for standard unicornscan output
        pattern = re.compile(r"TCP open\s+([\d\.]+):(\d+)\s+ttl")

        for line in raw_output.splitlines():
            match = pattern.search(line)
            if match:
                findings.append(
                    {"ip": match.group(1), "port": int(match.group(2)), "proto": "tcp"}
                )
        return {"open_ports": findings}

    def check_installed(self) -> bool:
        return shutil.which("unicornscan") is not None
