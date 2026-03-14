from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

class SessionState(str, Enum):
    CREATED="CREATED"; ACTIVE="ACTIVE"; IDLE="IDLE"; PAUSED="PAUSED"; CLOSED="CLOSED"

@dataclass
class SessionContext:
    session_id: str
    user_id: str
    channel: str
    state: SessionState = SessionState.CREATED
    message_history: list[dict] = field(default_factory=list)
    tool_usage: list[dict] = field(default_factory=list)
    context_window: list[str] = field(default_factory=list)
    memory_references: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
