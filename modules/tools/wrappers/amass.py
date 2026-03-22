import shutil
import json
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class AmassTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="amass",
            description="In-depth Attack Surface Mapping and Asset Discovery",
            category=ToolCategory.RECON,
            mode=ToolMode.OFFENSIVE,  # Can be considered offensive due to active scanning options, usually recon
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        if not input_data.target:
            return False
        return True

    def build_command(self, input_data: ToolInput) -> List[str]:
        # Default to 'enum' mode for enumeration
        cmd = ["amass", "enum", "-d", input_data.target, "-json", "amass_out.json"]

        if input_data.args.get("passive"):
            cmd.append("-passive")
        if input_data.args.get("active"):
            cmd.append("-active")

        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # Amass with -json writes to a file, but we might also capture stdout if needed.
        # For this wrapper, we assume the runner handles file reading or we parse stdout lines if they are json.
        # Here we will try to parse line-by-line JSON if provided in raw_output
        results = []
        for line in raw_output.splitlines():
            try:
                if line.strip().startswith("{"):
                    results.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        return {
            "subdomains": [r.get("name") for r in results if "name" in r],
            "raw_entries": results,
        }

    def check_installed(self) -> bool:
        return shutil.which("amass") is not None
