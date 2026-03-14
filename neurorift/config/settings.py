from dataclasses import dataclass
from pathlib import Path
@dataclass
class Settings:
    data_dir: Path = Path.home()/'.neurorift'
