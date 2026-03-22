import json
from pathlib import Path
from neurorift.sessions.session_context import SessionContext


class SessionStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, sid: str) -> Path:
        return self.root / f"{sid}.json"

    def save(self, session: SessionContext):
        self.path(session.session_id).write_text(
            json.dumps(session.__dict__, default=str), encoding="utf-8"
        )

    def load(self, sid: str):
        p = self.path(sid)
        return (
            SessionContext(**json.loads(p.read_text(encoding="utf-8")))
            if p.exists()
            else None
        )
