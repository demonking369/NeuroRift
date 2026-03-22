import shutil
import re
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class SqlmapTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="sqlmap",
            description="Automatic SQL injection and database takeover tool",
            category=ToolCategory.EXPLOITATION,
            mode=ToolMode.DEFENSIVE,  # Defaults to defensive (assessment)
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        return bool(input_data.target)

    def build_command(self, input_data: ToolInput) -> List[str]:
        cmd = [
            "sqlmap",
            "-u",
            input_data.target,
            "--batch",
        ]  # --batch for non-interactive

        # Risk / Level
        cmd.extend(["--risk", str(input_data.args.get("risk", 1))])
        cmd.extend(["--level", str(input_data.args.get("level", 1))])

        # Other common flags
        if input_data.args.get("crawl"):
            cmd.extend(["--crawl", str(input_data.args.get("crawl"))])
        if input_data.args.get("forms"):
            cmd.append("--forms")

        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        findings = []
        # Basic parsing of sqlmap output
        # "Parameter: id (GET)"
        # "Type: boolean-based blind"

        current_param = None

        for line in raw_output.splitlines():
            if line.startswith("Parameter:"):
                current_param = line.split(":")[1].strip()
            elif line.startswith("    Type:"):
                vuln_type = line.split(":")[1].strip()
                findings.append({"parameter": current_param, "type": vuln_type})

        return {"vulnerabilities": findings}

    def check_installed(self) -> bool:
        return shutil.which("sqlmap") is not None
