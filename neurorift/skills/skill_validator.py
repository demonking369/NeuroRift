from pathlib import Path


class SkillValidator:
    required = ["skill.json", "skill.py", "README.md"]

    def validate(self, path: Path):
        missing = [f for f in self.required if not (path / f).exists()]
        return (len(missing) == 0, missing)
