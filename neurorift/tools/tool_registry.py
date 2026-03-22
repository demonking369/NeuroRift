class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name, meta):
        self.tools[name] = meta
