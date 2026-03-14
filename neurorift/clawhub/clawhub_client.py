from pathlib import Path
import shutil


class ClawHubClient:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_skill(self, skill_name: str, source_dir: Path) -> Path:
        src = source_dir / skill_name
        if not src.exists():
            raise FileNotFoundError(skill_name)
        dst = self.cache_dir / skill_name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return dst
