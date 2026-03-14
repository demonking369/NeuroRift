import json, shutil
from pathlib import Path
from neurorift.skills.skill_validator import SkillValidator
from neurorift.skills.registry import SkillRegistry

class SkillInstaller:
    def __init__(self, base: Path):
        self.base=base; self.installed=base/'installed'; self.cache=base/'cache'
        self.installed.mkdir(parents=True, exist_ok=True); self.cache.mkdir(parents=True, exist_ok=True)
        self.validator=SkillValidator(); self.registry=SkillRegistry(base)
    def install(self, pkg: Path):
        ok,missing=self.validator.validate(pkg)
        if not ok: return {'success': False, 'error': f'missing:{missing}'}
        meta=json.loads((pkg/'skill.json').read_text(encoding='utf-8')); name=meta['name']
        dst=self.installed/name
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(pkg,dst)
        self.registry.add(name)
        return {'success': True, 'name': name, 'path': str(dst)}
    def uninstall(self, name: str):
        dst=self.installed/name
        if dst.exists(): shutil.rmtree(dst)
        self.registry.remove(name)
        return {'success': True, 'name': name}
