#!/usr/bin/env python3
"""
NeuroRift Session Manager
Manages session lifecycle, persistence, and state management.

Designed and developed by demonking369
"""

import json
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SessionStatus(Enum):
    """Session status states"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionManager:
    """
    Core session management for NeuroRift.

    Handles:
    - Session creation, loading, saving, deletion
    - Session lifecycle management
    - Session indexing and discovery
    - Auto-save coordination
    """

    NRS_VERSION = "1.0"

    def __init__(self, base_dir: str = "~/.neurorift"):
        self.base_dir = Path(base_dir).expanduser()
        self.sessions_dir = self.base_dir / "sessions"
        self.session_data_dir = self.base_dir / "session_data"
        self.logger = logging.getLogger(__name__)

        # Session directories
        self.active_dir = self.sessions_dir / "active"
        self.paused_dir = self.sessions_dir / "paused"
        self.completed_dir = self.sessions_dir / "completed"
        self.archived_dir = self.sessions_dir / "archived"

        # Current session
        self.current_session_id: Optional[str] = None
        self.current_session_data: Optional[Dict] = None

        # Initialize
        self._setup_directories()
        self._load_index()

    def _setup_directories(self):
        """Create session directory structure"""
        for directory in [
            self.sessions_dir,
            self.session_data_dir,
            self.active_dir,
            self.paused_dir,
            self.completed_dir,
            self.archived_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        self.logger.info("Session directories initialized")

    def _load_index(self):
        """Load session index"""
        index_path = self.sessions_dir / "session_index.json"

        if index_path.exists():
            try:
                with open(index_path, "r") as f:
                    self.index = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading session index: {e}")
                self.index = {"sessions": {}, "last_active": None}
        else:
            self.index = {"sessions": {}, "last_active": None}

    def _save_index(self):
        """Save session index"""
        index_path = self.sessions_dir / "session_index.json"

        try:
            with open(index_path, "w") as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving session index: {e}")

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        return f"session_{timestamp}_{unique_id}"

    def create_session(
        self, name: Optional[str] = None, mode: str = "offensive", description: str = ""
    ) -> str:
        """
        Create a new session.

        Args:
            name: Session name (auto-generated if None)
            mode: Operational mode (offensive/defensive)
            description: Session description

        Returns:
            Session ID
        """
        session_id = self._generate_session_id()

        if not name:
            name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Create session data structure
        session_data = {
            "nrs_version": self.NRS_VERSION,
            "session": {
                "id": session_id,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": SessionStatus.ACTIVE.value,
                "mode": mode,
                "description": description,
            },
            "conversation": {
                "messages": [],
                "context": {
                    "system_prompt": "",
                    "current_agent": None,
                    "agent_state": {},
                },
            },
            "task_state": {
                "task_id": None,
                "task_type": None,
                "target": None,
                "progress": {
                    "total_steps": 0,
                    "completed_steps": 0,
                    "current_step": 0,
                    "percentage": 0,
                },
                "plan": {},
                "execution_state": {},
            },
            "tools_state": {
                "active_tools": [],
                "tool_outputs": {},
                "pending_approvals": [],
            },
            "mode_state": {
                "current_mode": mode,
                "mode_governor_state": {"violations": [], "allowed_tools": []},
            },
            "results": {
                "output_dir": str(self.session_data_dir / session_id / "results"),
                "artifacts": [],
                "reports": [],
            },
            "metadata": {
                "neurorift_version": "1.0.0",
                "python_version": "3.10+",
                "platform": "linux",
                "tags": [],
                "notes": "",
            },
        }

        # Create session data directory
        session_dir = self.session_data_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "results").mkdir(exist_ok=True)
        (session_dir / "logs").mkdir(exist_ok=True)
        (session_dir / "artifacts").mkdir(exist_ok=True)

        # Save session file
        self._save_session_file(session_id, session_data, SessionStatus.ACTIVE)

        # Update index
        self.index["sessions"][session_id] = {
            "name": name,
            "status": SessionStatus.ACTIVE.value,
            "mode": mode,
            "created_at": session_data["session"]["created_at"],
            "updated_at": session_data["session"]["updated_at"],
        }
        self.index["last_active"] = session_id
        self._save_index()

        # Set as current session
        self.current_session_id = session_id
        self.current_session_data = session_data

        self.logger.info(f"Created session: {session_id} ({name})")
        return session_id

    def _save_session_file(
        self, session_id: str, session_data: Dict, status: SessionStatus
    ):
        """Save session to .nrs file"""
        # Determine directory based on status
        if status == SessionStatus.ACTIVE:
            target_dir = self.active_dir
        elif status == SessionStatus.PAUSED:
            target_dir = self.paused_dir
        elif status == SessionStatus.COMPLETED:
            target_dir = self.completed_dir
        else:
            target_dir = self.paused_dir

        session_file = target_dir / f"{session_id}.nrs"

        # Update status in data
        session_data["session"]["status"] = status.value
        session_data["session"]["updated_at"] = datetime.now().isoformat()

        # Atomic write (write to temp, then rename)
        temp_file = session_file.with_suffix(".nrs.tmp")
        try:
            with open(temp_file, "w") as f:
                json.dump(session_data, f, indent=2)
            temp_file.rename(session_file)
            self.logger.debug(f"Saved session file: {session_file}")
        except Exception as e:
            self.logger.error(f"Error saving session file: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def save_session(self, session_id: Optional[str] = None, notes: str = ""):
        """
        Save current or specified session.

        Args:
            session_id: Session ID (uses current if None)
            notes: Optional notes to add to metadata
        """
        if not session_id:
            session_id = self.current_session_id

        if not session_id:
            raise ValueError("No active session to save")

        if not self.current_session_data:
            raise ValueError("No session data loaded")

        # Update metadata
        if notes:
            self.current_session_data["metadata"]["notes"] = notes

        # Save to paused directory
        self._save_session_file(
            session_id, self.current_session_data, SessionStatus.PAUSED
        )

        # Update index
        self.index["sessions"][session_id]["status"] = SessionStatus.PAUSED.value
        self.index["sessions"][session_id]["updated_at"] = datetime.now().isoformat()
        self._save_index()

        # Remove from active directory if exists
        active_file = self.active_dir / f"{session_id}.nrs"
        if active_file.exists():
            active_file.unlink()

        self.logger.info(f"Saved session: {session_id}")

    def load_session(self, session_id: str) -> Dict:
        """
        Load a session from file.

        Args:
            session_id: Session ID to load

        Returns:
            Session data dictionary
        """
        # Search for session file in all directories
        for directory in [self.active_dir, self.paused_dir, self.completed_dir]:
            session_file = directory / f"{session_id}.nrs"
            if session_file.exists():
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)

                    # Validate version
                    if session_data.get("nrs_version") != self.NRS_VERSION:
                        self.logger.warning(
                            f"Session version mismatch: {session_data.get('nrs_version')} != {self.NRS_VERSION}"
                        )
                        # TODO: Implement migration

                    self.current_session_id = session_id
                    self.current_session_data = session_data

                    self.logger.info(f"Loaded session: {session_id}")
                    return session_data

                except Exception as e:
                    self.logger.error(f"Error loading session {session_id}: {e}")
                    raise

        raise FileNotFoundError(f"Session not found: {session_id}")

    def resume_session(self, session_id: Optional[str] = None) -> Dict:
        """
        Resume a paused session.

        Args:
            session_id: Session ID (uses last active if None)

        Returns:
            Session data dictionary
        """
        if not session_id:
            session_id = self.index.get("last_active")

        if not session_id:
            raise ValueError("No session to resume")

        # Load session
        session_data = self.load_session(session_id)

        # Move to active directory
        self._save_session_file(session_id, session_data, SessionStatus.ACTIVE)

        # Remove from paused directory
        paused_file = self.paused_dir / f"{session_id}.nrs"
        if paused_file.exists():
            paused_file.unlink()

        # Update index
        self.index["sessions"][session_id]["status"] = SessionStatus.ACTIVE.value
        self.index["last_active"] = session_id
        self._save_index()

        self.logger.info(f"Resumed session: {session_id}")
        return session_data

    def list_sessions(
        self, status: Optional[str] = None, mode: Optional[str] = None
    ) -> List[Dict]:
        """
        List all sessions with optional filtering.

        Args:
            status: Filter by status (active/paused/completed)
            mode: Filter by mode (offensive/defensive)

        Returns:
            List of session metadata
        """
        sessions = []

        for session_id, metadata in self.index["sessions"].items():
            # Apply filters
            if status and metadata.get("status") != status:
                continue
            if mode and metadata.get("mode") != mode:
                continue

            sessions.append({"id": session_id, **metadata})

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return sessions

    def delete_session(self, session_id: str, force: bool = False):
        """
        Delete a session.

        Args:
            session_id: Session ID to delete
            force: Skip confirmation if True
        """
        if not force:
            # In CLI, this would prompt for confirmation
            self.logger.warning(f"Deleting session: {session_id}")

        # Remove session file from all directories
        for directory in [
            self.active_dir,
            self.paused_dir,
            self.completed_dir,
            self.archived_dir,
        ]:
            session_file = directory / f"{session_id}.nrs"
            if session_file.exists():
                session_file.unlink()

        # Remove session data directory
        session_dir = self.session_data_dir / session_id
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)

        # Remove from index
        if session_id in self.index["sessions"]:
            del self.index["sessions"][session_id]

        if self.index.get("last_active") == session_id:
            self.index["last_active"] = None

        self._save_index()

        self.logger.info(f"Deleted session: {session_id}")

    def rename_session(self, session_id: str, new_name: str):
        """
        Rename a session.

        Args:
            session_id: Session ID to rename
            new_name: New session name
        """
        # Load session
        session_data = self.load_session(session_id)

        # Update name
        session_data["session"]["name"] = new_name
        session_data["session"]["updated_at"] = datetime.now().isoformat()

        # Save
        status = SessionStatus(session_data["session"]["status"])
        self._save_session_file(session_id, session_data, status)

        # Update index
        self.index["sessions"][session_id]["name"] = new_name
        self.index["sessions"][session_id]["updated_at"] = datetime.now().isoformat()
        self._save_index()

        self.logger.info(f"Renamed session {session_id} to: {new_name}")

    def get_current_session(self) -> Optional[Dict]:
        """Get current active session data"""
        return self.current_session_data

    def update_session_state(self, updates: Dict):
        """
        Update current session state.

        Args:
            updates: Dictionary of updates to apply
        """
        if not self.current_session_data:
            raise ValueError("No active session")

        # Deep merge updates
        self._deep_merge(self.current_session_data, updates)

        # Update timestamp
        self.current_session_data["session"]["updated_at"] = datetime.now().isoformat()

    def _deep_merge(self, base: Dict, updates: Dict):
        """Deep merge updates into base dictionary"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize session manager
    manager = SessionManager()

    # Create new session
    session_id = manager.create_session(
        name="Example.com Security Assessment",
        mode="offensive",
        description="Full security assessment",
    )

    print(f"Created session: {session_id}")

    # Update session state
    manager.update_session_state(
        {"task_state": {"target": "example.com", "task_type": "reconnaissance"}}
    )

    # Save session
    manager.save_session(notes="Pausing for lunch")

    # List sessions
    sessions = manager.list_sessions()
    print(f"\nSessions: {len(sessions)}")
    for session in sessions:
        print(f"  - {session['id']}: {session['name']} ({session['status']})")

    # Resume session
    manager.resume_session(session_id)
    print(f"\nResumed session: {session_id}")
