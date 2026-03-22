from pathlib import Path
from neurorift.clawhub.clawhub_client import ClawHubClient
from neurorift.skills.installer import SkillInstaller
from neurorift.skills.loader import SkillLoader


class SkillManager:
    def __init__(self, home: Path):
        self.base = home / "skills"
        self.installer = SkillInstaller(self.base)
        self.loader = SkillLoader()
        self.client = ClawHubClient(self.installer.cache)
        self.examples = (
            Path(__file__).resolve().parents[1] / "skill_store" / "installed"
        )

    def install_clawhub(self, skill_name: str):
        pkg = self.client.fetch_skill(skill_name, self.examples)
        return self.installer.install(pkg)

    def list(self):
        return self.installer.registry.list()

    def run(self, skill_name: str, **kwargs):
        return self.loader.run(self.installer.installed / skill_name, **kwargs)

    def uninstall(self, skill_name: str):
        return self.installer.uninstall(skill_name)
