import shutil
import re
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class IkeScanTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="ike-scan",
            description="Discover and fingerprint IKE hosts (IPsec VPN Servers)",
            category=ToolCategory.RECON,
            mode=ToolMode.OFFENSIVE,
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        return bool(input_data.target)

    def build_command(self, input_data: ToolInput) -> List[str]:
        cmd = ["ike-scan", "-M"]  # -M for multiline output (better for parsing)
        cmd.append(input_data.target)
        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        hosts = []
        # Basic parsing looking for "Handshake returned"
        # 192.168.1.1 Notify message 14 (NO_PROPOSAL_CHOSEN)
        # OR 192.168.1.1 Main Mode Handshake returned

        for line in raw_output.splitlines():
            if "Handshake returned" in line or "Notify message" in line:
                parts = line.split()
                if parts:
                    hosts.append({"ip": parts[0], "details": line})
        return {"ike_hosts": hosts}

    def check_installed(self) -> bool:
        return shutil.which("ike-scan") is not None
