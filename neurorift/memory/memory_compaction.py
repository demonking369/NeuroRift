class MemoryCompaction:
    def compact(self, messages: list[str]): return {"summary": " ".join(messages[:10]), "kept": messages[-10:]}
