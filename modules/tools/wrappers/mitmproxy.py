import shutil
from typing import Dict, Any, List
from modules.tools.base import BaseTool, ToolCategory, ToolMode, ToolInput


class MitmproxyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="mitmproxy",
            description="Interceptor for HTTP/HTTPS traffic (via mitmdump)",
            category=ToolCategory.EXPLOITATION,  # /Analysis
            mode=ToolMode.DEFENSIVE,
        )

    def validate_input(self, input_data: ToolInput) -> bool:
        # Usually needs a port to listen on or a file to write to
        return True

    def build_command(self, input_data: ToolInput) -> List[str]:
        # Use mitmdump for non-interactive
        cmd = ["mitmdump"]

        port = input_data.args.get("port", 8080)
        cmd.extend(["-p", str(port)])

        script = input_data.args.get("script")
        if script:
            cmd.extend(["-s", script])

        outfile = input_data.args.get("outfile")
        if outfile:
            cmd.extend(["-w", outfile])

        return cmd

    def parse_output(self, raw_output: str) -> Dict[str, Any]:
        # mitmdump output is mostly logs.
        # We rely on the outfile or script side-effects mostly.
        return {"logs": raw_output}

    def check_installed(self) -> bool:
        return shutil.which("mitmdump") is not None
