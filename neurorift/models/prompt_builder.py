class PromptBuilder:
    def build(self, message: str, context: dict): return f"{context}\n{message}"
