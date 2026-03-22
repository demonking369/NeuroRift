import shutil
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class NmapTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="nmap",
            description="Network exploration tool and security / port scanner",
            category=ToolCategory.RECON,
            mode=ToolMode.OFFENSIVE,  # Active scanning
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        return bool(input_data.target)

    def build_command(self, input_data: ToolInput) -> List[str]:
        # Always output valid XML for easy parsing
        cmd = ["nmap", "-oX", "-"]

        flags = input_data.args.get("flags", [])
        if flags:
            cmd.extend(flags)
        else:
            # Default safe scan
            cmd.extend(["-sV", "-F"])  # Version detection, Fast scan

        cmd.append(input_data.target)
        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # Parse XML output from stdout
        try:
            root = ET.fromstring(raw_output)
            hosts = []
            for host in root.findall("host"):
                address = host.find("address").get("addr")
                ports = []
                ports_elem = host.find("ports")
                if ports_elem:
                    for port in ports_elem.findall("port"):
                        port_id = port.get("portid")
                        state = port.find("state").get("state")
                        service = port.find("service")
                        service_name = (
                            service.get("name") if service is not None else "unknown"
                        )
                        ports.append(
                            {"port": port_id, "state": state, "service": service_name}
                        )
                hosts.append({"ip": address, "ports": ports})
            return {"hosts": hosts}
        except ET.ParseError:
            return {"error": "Failed to parse Nmap XML", "raw": raw_output[:500]}

    def check_installed(self) -> bool:
        return shutil.which("nmap") is not None
