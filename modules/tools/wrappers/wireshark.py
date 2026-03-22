import shutil
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class WiresharkTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="wireshark",
            description="Network protocol analyzer (using tshark)",
            category=ToolCategory.MONITORING,
            mode=ToolMode.DEFENSIVE,
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        # Needs interface or file
        return bool(input_data.args.get("interface")) or bool(
            input_data.args.get("read_file")
        )

    def build_command(self, input_data: ToolInput) -> List[str]:
        cmd = ["tshark"]

        interface = input_data.args.get("interface")
        if interface:
            cmd.extend(["-i", interface])

        read_file = input_data.args.get("read_file")
        if read_file:
            cmd.extend(["-r", read_file])

        write_file = input_data.args.get("write_file")
        if write_file:
            cmd.extend(["-w", write_file])

        # JSON output for easier parsing
        cmd.extend(["-T", "json"])

        count = input_data.args.get("packet_count")
        if count:
            cmd.extend(["-c", str(count)])

        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # tshark -T json outputs a JSON array of packets
        import json

        try:
            packets = json.loads(raw_output)
            return {"packets": packets, "count": len(packets)}
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON output", "raw": raw_output[:500]}

    def check_installed(self) -> bool:
        return shutil.which("tshark") is not None
