from dataclasses import dataclass
from neurorift.core.agent_loop import AgentLoop
from neurorift.sessions.session_manager import SessionManager


@dataclass
class AgentHandle:
    session_id: str
    user_id: str
    channel: str


class AgentManager:
    def __init__(self, session_manager: SessionManager, agent_loop: AgentLoop):
        self.session_manager = session_manager
        self.agent_loop = agent_loop
        self.handles: dict[str, AgentHandle] = {}
