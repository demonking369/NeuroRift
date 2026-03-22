class ModelRouter:
    async def generate(self, prompt: str):
        return {
            "response": prompt,
            "model": "openai",
            "tokens": len(prompt.split()),
            "cost": 0.0,
        }
