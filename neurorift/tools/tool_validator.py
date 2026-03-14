class ToolValidator:
    def validate(self, tool_call: dict):
        return bool(tool_call.get("name")), None
