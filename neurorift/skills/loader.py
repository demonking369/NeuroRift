import importlib.util, json
from pathlib import Path
class SkillLoader:
    def run(self, skill_dir: Path, **kwargs):
        meta=json.loads((skill_dir/'skill.json').read_text(encoding='utf-8'))
        entry=skill_dir/meta['entrypoint']
        spec=importlib.util.spec_from_file_location(f"skill_{meta['name']}", entry)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod.run(**kwargs) if hasattr(mod, 'run') else {'error':'missing run()'}
