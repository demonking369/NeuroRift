import json
from pathlib import Path


class SkillRegistry:
    def __init__(self, root: Path):
        self.path = root / "registry.json"
        root.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(
                json.dumps({"installed_skills": []}, indent=2), encoding="utf-8"
            )

    def read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def list(self):
        return self.read().get("installed_skills", [])

    def add(self, name):
        data = self.read()
        skills = data.setdefault("installed_skills", [])
        if name not in skills:
            skills.append(name)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def remove(self, name):
        data = self.read()
        data["installed_skills"] = [
            s for s in data.get("installed_skills", []) if s != name
        ]
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
