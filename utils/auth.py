#!/usr/bin/env python3
"""
NeuroRift Authentication and Authorization Framework
Provides session management and role-based access control
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

from utils.security_utils import TokenGenerator, FilePermissionManager

logger = logging.getLogger(__name__)


class Role(Enum):
    """User roles for RBAC"""

    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class Permission(Enum):
    """Permissions for different operations"""

    # AI Operations
    AI_QUERY = "ai_query"
    AI_GENERATE_TOOL = "ai_generate_tool"

    # Scanning Operations
    SCAN_TARGET = "scan_target"
    SCAN_AGGRESSIVE = "scan_aggressive"

    # Report Operations
    REPORT_GENERATE = "report_generate"
    REPORT_VIEW = "report_view"
    REPORT_DELETE = "report_delete"

    # Session Operations
    SESSION_CREATE = "session_create"
    SESSION_VIEW = "session_view"
    SESSION_DELETE = "session_delete"

    # Configuration Operations
    CONFIG_READ = "config_read"
    CONFIG_WRITE = "config_write"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.AI_QUERY,
        Permission.AI_GENERATE_TOOL,
        Permission.SCAN_TARGET,
        Permission.SCAN_AGGRESSIVE,
        Permission.REPORT_GENERATE,
        Permission.REPORT_VIEW,
        Permission.REPORT_DELETE,
        Permission.SESSION_CREATE,
        Permission.SESSION_VIEW,
        Permission.SESSION_DELETE,
        Permission.CONFIG_READ,
        Permission.CONFIG_WRITE,
    ],
    Role.USER: [
        Permission.AI_QUERY,
        Permission.AI_GENERATE_TOOL,
        Permission.SCAN_TARGET,
        Permission.REPORT_GENERATE,
        Permission.REPORT_VIEW,
        Permission.SESSION_CREATE,
        Permission.SESSION_VIEW,
        Permission.CONFIG_READ,
    ],
    Role.READONLY: [
        Permission.REPORT_VIEW,
        Permission.SESSION_VIEW,
        Permission.CONFIG_READ,
    ],
}


@dataclass
class User:
    """User data class"""

    username: str
    role: Role
    created_at: float
    last_login: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["role"] = self.role.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create from dictionary"""
        data["role"] = Role(data["role"])
        return cls(**data)


@dataclass
class Session:
    """Session data class"""

    session_id: str
    username: str
    created_at: float
    expires_at: float
    last_activity: float

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return time.time() > self.expires_at

    def is_active(self, timeout: int = 3600) -> bool:
        """Check if session is still active

        Args:
            timeout: Inactivity timeout in seconds (default: 1 hour)
        """
        return time.time() - self.last_activity < timeout

    def refresh(self) -> None:
        """Refresh session activity timestamp"""
        self.last_activity = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create from dictionary"""
        return cls(**data)


class AuthManager:
    """Manages authentication and authorization"""

    def __init__(self, auth_dir: Optional[Path] = None):
        """Initialize auth manager

        Args:
            auth_dir: Directory to store auth data (default: ~/.neurorift/auth)
        """
        if auth_dir is None:
            auth_dir = Path.home() / ".neurorift" / "auth"

        self.auth_dir = Path(auth_dir)
        FilePermissionManager.create_secure_directory(self.auth_dir, mode=0o700)

        self.users_file = self.auth_dir / "users.json"
        self.sessions_file = self.auth_dir / "sessions.json"

        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}

        self._load_users()
        self._load_sessions()

        # Create default admin user if no users exist
        if not self.users:
            self._create_default_admin()

    def _load_users(self) -> None:
        """Load users from file"""
        if not self.users_file.exists():
            return

        try:
            with open(self.users_file, "r") as f:
                data = json.load(f)
                self.users = {
                    username: User.from_dict(user_data)
                    for username, user_data in data.items()
                }
        except Exception as e:
            logger.error("Error loading users: %s", e)

    def _save_users(self) -> None:
        """Save users to file"""
        try:
            data = {username: user.to_dict() for username, user in self.users.items()}

            with open(self.users_file, "w") as f:
                json.dump(data, f, indent=2)

            FilePermissionManager.set_secure_permissions(self.users_file, mode=0o600)

        except Exception as e:
            logger.error("Error saving users: %s", e)

    def _load_sessions(self) -> None:
        """Load sessions from file"""
        if not self.sessions_file.exists():
            return

        try:
            with open(self.sessions_file, "r") as f:
                data = json.load(f)
                self.sessions = {
                    session_id: Session.from_dict(session_data)
                    for session_id, session_data in data.items()
                }

            # Clean up expired sessions
            self._cleanup_sessions()

        except Exception as e:
            logger.error("Error loading sessions: %s", e)

    def _save_sessions(self) -> None:
        """Save sessions to file"""
        try:
            data = {
                session_id: session.to_dict()
                for session_id, session in self.sessions.items()
            }

            with open(self.sessions_file, "w") as f:
                json.dump(data, f, indent=2)

            FilePermissionManager.set_secure_permissions(self.sessions_file, mode=0o600)

        except Exception as e:
            logger.error("Error saving sessions: %s", e)

    def _cleanup_sessions(self) -> None:
        """Remove expired and inactive sessions"""
        expired = [
            sid
            for sid, session in self.sessions.items()
            if session.is_expired() or not session.is_active()
        ]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            self._save_sessions()

    def _create_default_admin(self) -> None:
        """Create default admin user"""
        admin_user = User(username="admin", role=Role.ADMIN, created_at=time.time())

        self.users["admin"] = admin_user
        self._save_users()

        logger.info("Created default admin user")

    def create_user(self, username: str, role: Role = Role.USER) -> bool:
        """Create a new user

        Args:
            username: Username
            role: User role

        Returns:
            True if successful, False otherwise
        """
        if username in self.users:
            logger.warning("User already exists: %s", username)
            return False

        user = User(username=username, role=role, created_at=time.time())

        self.users[username] = user
        self._save_users()

        logger.info("Created user: %s with role %s", username, role.value)
        return True

    def create_session(self, username: str, duration: int = 86400) -> Optional[str]:
        """Create a new session for user

        Args:
            username: Username
            duration: Session duration in seconds (default: 24 hours)

        Returns:
            Session ID or None if failed
        """
        if username not in self.users:
            logger.warning("User not found: %s", username)
            return None

        # Update last login
        self.users[username].last_login = time.time()
        self._save_users()

        # Create session
        session_id = TokenGenerator.generate_token(32)
        now = time.time()

        session = Session(
            session_id=session_id,
            username=username,
            created_at=now,
            expires_at=now + duration,
            last_activity=now,
        )

        self.sessions[session_id] = session
        self._save_sessions()

        logger.info("Created session for user: %s", username)
        return session_id

    def validate_session(self, session_id: str) -> Optional[Session]:
        """Validate session and return session object

        Args:
            session_id: Session ID to validate

        Returns:
            Session object if valid, None otherwise
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        if session.is_expired() or not session.is_active():
            del self.sessions[session_id]
            self._save_sessions()
            return None

        # Refresh activity timestamp
        session.refresh()
        self._save_sessions()

        return session

    def get_user(self, username: str) -> Optional[User]:
        """Get user by username

        Args:
            username: Username

        Returns:
            User object or None if not found
        """
        return self.users.get(username)

    def has_permission(self, username: str, permission: Permission) -> bool:
        """Check if user has permission

        Args:
            username: Username
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        user = self.get_user(username)
        if not user:
            return False

        allowed_permissions = ROLE_PERMISSIONS.get(user.role, [])
        return permission in allowed_permissions

    def require_permission(self, session_id: str, permission: Permission) -> bool:
        """Require permission for operation

        Args:
            session_id: Session ID
            permission: Required permission

        Returns:
            True if authorized, False otherwise

        Raises:
            PermissionError: If not authorized
        """
        session = self.validate_session(session_id)
        if not session:
            raise PermissionError("Invalid or expired session")

        if not self.has_permission(session.username, permission):
            raise PermissionError(
                f"User {session.username} does not have permission: {permission.value}"
            )

        return True

    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session

        Args:
            session_id: Session ID to destroy

        Returns:
            True if successful, False otherwise
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            logger.info("Destroyed session: %s", session_id)
            return True

        return False


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
