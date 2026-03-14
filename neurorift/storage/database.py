from pathlib import Path
class Database:
    def __init__(self, root: Path): self.root=root; root.mkdir(parents=True, exist_ok=True)
