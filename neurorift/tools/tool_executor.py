class ToolExecutor:
    def execute(self, tool_call: dict):
        return {"success": True, "tool_call": tool_call}
