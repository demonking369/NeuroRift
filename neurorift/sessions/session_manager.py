import uuid
from pathlib import Path
from neurorift.sessions.session_context import SessionContext, SessionState
from neurorift.sessions.session_store import SessionStore

class SessionManager:
    def __init__(self, root: Path):
        self.store = SessionStore(root)
        self.sessions: dict[str, SessionContext] = {}
    def create_session(self, user_id: str, channel: str) -> SessionContext:
        sid=str(uuid.uuid4()); s=SessionContext(session_id=sid,user_id=user_id,channel=channel,state=SessionState.ACTIVE)
        self.sessions[sid]=s; self.store.save(s); return s
    def get_session(self, sid: str): return self.sessions.get(sid) or self.store.load(sid)
