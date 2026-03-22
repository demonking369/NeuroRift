import shutil
import re
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class MasscanTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="masscan",
            description="Mass IP port scanner",
            category=ToolCategory.RECON,
            mode=ToolMode.OFFENSIVE,  # Active scanning is offensive
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        if not input_data.target:
            return False
        # Masscan needs ports usually
        if not input_data.args.get("ports"):
            # Default to top ports or require it? Let's default to a safe small range for demo
            pass
        return True

    def build_command(self, input_data: ToolInput) -> List[str]:
        target = input_data.target
        ports = input_data.args.get("ports", "80,443")
        rate = input_data.args.get("rate", "100")

        cmd = ["masscan", target, "-p", ports, "--rate", str(rate)]

        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # Masscan output example: Discovered open port 80/tcp on 192.168.1.1
        findings = []
        pattern = re.compile(r"Discovered open port (\d+)/(\w+) on ([\d\.]+)")

        for line in raw_output.splitlines():
            match = pattern.search(line)
            if match:
                findings.append(
                    {
                        "port": int(match.group(1)),
                        "proto": match.group(2),
                        "ip": match.group(3),
                    }
                )

        return {"open_ports": findings}

    def check_installed(self) -> bool:
        return shutil.which("masscan") is not None
