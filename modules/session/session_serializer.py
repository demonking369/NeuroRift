#!/usr/bin/env python3
"""
NeuroRift Session Serializer
Handles serialization/deserialization of session state to .nrs format.

Designed and developed by demonking369
"""

import json
import gzip
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class SessionSerializer:
    """
    Handles conversion between Python objects and .nrs file format.

    Features:
    - JSON serialization/deserialization
    - Schema validation
    - Version handling
    - Optional compression for large sessions
    """

    SUPPORTED_VERSIONS = ["1.0"]
    CURRENT_VERSION = "1.0"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def serialize(self, session_data: Dict, compress: bool = False) -> bytes:
        """
        Serialize session data to bytes.

        Args:
            session_data: Session data dictionary
            compress: Enable gzip compression

        Returns:
            Serialized bytes
        """
        try:
            # Validate schema
            self._validate_schema(session_data)

            # Convert to JSON
            json_str = json.dumps(session_data, indent=2, ensure_ascii=False)
            json_bytes = json_str.encode("utf-8")

            # Compress if requested
            if compress:
                json_bytes = gzip.compress(json_bytes)
                self.logger.debug("Session data compressed")

            return json_bytes

        except Exception as e:
            self.logger.error(f"Serialization error: {e}")
            raise

    def deserialize(self, data: bytes, decompress: bool = False) -> Dict:
        """
        Deserialize session data from bytes.

        Args:
            data: Serialized bytes
            decompress: Enable gzip decompression

        Returns:
            Session data dictionary
        """
        try:
            # Decompress if needed
            if decompress:
                data = gzip.decompress(data)
                self.logger.debug("Session data decompressed")

            # Parse JSON
            json_str = data.decode("utf-8")
            session_data = json.loads(json_str)

            # Validate schema
            self._validate_schema(session_data)

            # Check version compatibility
            version = session_data.get("nrs_version")
            if version not in self.SUPPORTED_VERSIONS:
                self.logger.warning(f"Unsupported session version: {version}")
                # Attempt migration
                session_data = self._migrate_version(session_data, version)

            return session_data

        except Exception as e:
            self.logger.error(f"Deserialization error: {e}")
            raise

    def save_to_file(self, session_data: Dict, file_path: Path, compress: bool = False):
        """
        Save session data to .nrs file.

        Args:
            session_data: Session data dictionary
            file_path: Path to .nrs file
            compress: Enable compression
        """
        try:
            # Serialize
            data = self.serialize(session_data, compress=compress)

            # Atomic write
            temp_path = file_path.with_suffix(".nrs.tmp")
            with open(temp_path, "wb") as f:
                f.write(data)

            # Rename to final path
            temp_path.rename(file_path)

            self.logger.info(f"Session saved to: {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving session file: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_from_file(self, file_path: Path, decompress: bool = False) -> Dict:
        """
        Load session data from .nrs file.

        Args:
            file_path: Path to .nrs file
            decompress: Enable decompression

        Returns:
            Session data dictionary
        """
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            session_data = self.deserialize(data, decompress=decompress)

            self.logger.info(f"Session loaded from: {file_path}")
            return session_data

        except Exception as e:
            self.logger.error(f"Error loading session file: {e}")
            raise

    def _validate_schema(self, session_data: Dict):
        """
        Validate session data schema.

        Args:
            session_data: Session data to validate

        Raises:
            ValueError: If schema is invalid
        """
        required_fields = [
            "nrs_version",
            "session",
            "conversation",
            "task_state",
            "tools_state",
            "mode_state",
            "results",
            "metadata",
        ]

        for field in required_fields:
            if field not in session_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate session section
        session_required = ["id", "name", "created_at", "status", "mode"]
        for field in session_required:
            if field not in session_data["session"]:
                raise ValueError(f"Missing session field: {field}")

        self.logger.debug("Schema validation passed")

    def _migrate_version(self, session_data: Dict, from_version: str) -> Dict:
        """
        Migrate session data from old version to current.

        Args:
            session_data: Session data to migrate
            from_version: Source version

        Returns:
            Migrated session data
        """
        self.logger.info(
            f"Migrating session from v{from_version} to v{self.CURRENT_VERSION}"
        )

        # Migration logic would go here
        # For now, just update version
        session_data["nrs_version"] = self.CURRENT_VERSION

        return session_data

    def export_session(
        self, session_data: Dict, export_path: Path, include_data: bool = True
    ):
        """
        Export session to portable format.

        Args:
            session_data: Session data to export
            export_path: Export directory
            include_data: Include session data directory
        """
        try:
            export_path.mkdir(parents=True, exist_ok=True)

            # Save session file
            session_file = export_path / f"{session_data['session']['id']}.nrs"
            self.save_to_file(session_data, session_file, compress=True)

            # Copy session data if requested
            if include_data:
                # TODO: Copy session_data directory
                pass

            self.logger.info(f"Session exported to: {export_path}")

        except Exception as e:
            self.logger.error(f"Export error: {e}")
            raise

    def import_session(self, import_path: Path, sessions_dir: Path) -> str:
        """
        Import session from exported format.

        Args:
            import_path: Path to exported session
            sessions_dir: Target sessions directory

        Returns:
            Imported session ID
        """
        try:
            # Find .nrs file
            nrs_files = list(import_path.glob("*.nrs"))
            if not nrs_files:
                raise FileNotFoundError("No .nrs file found in import path")

            session_file = nrs_files[0]

            # Load session
            session_data = self.load_from_file(session_file, decompress=True)
            session_id = session_data["session"]["id"]

            # Copy to sessions directory
            target_file = sessions_dir / "paused" / f"{session_id}.nrs"
            self.save_to_file(session_data, target_file)

            self.logger.info(f"Session imported: {session_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Import error: {e}")
            raise

    def create_checkpoint(self, session_data: Dict, checkpoint_dir: Path):
        """
        Create a checkpoint of current session state.

        Args:
            session_data: Session data to checkpoint
            checkpoint_dir: Directory for checkpoints
        """
        try:
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = checkpoint_dir / f"checkpoint_{timestamp}.nrs"

            self.save_to_file(session_data, checkpoint_file, compress=True)

            # Keep only last 10 checkpoints
            checkpoints = sorted(checkpoint_dir.glob("checkpoint_*.nrs"))
            if len(checkpoints) > 10:
                for old_checkpoint in checkpoints[:-10]:
                    old_checkpoint.unlink()

            self.logger.debug(f"Checkpoint created: {checkpoint_file}")

        except Exception as e:
            self.logger.error(f"Checkpoint error: {e}")

    def restore_from_checkpoint(
        self, checkpoint_dir: Path, checkpoint_index: int = -1
    ) -> Dict:
        """
        Restore session from checkpoint.

        Args:
            checkpoint_dir: Directory containing checkpoints
            checkpoint_index: Index of checkpoint (-1 for latest)

        Returns:
            Restored session data
        """
        try:
            checkpoints = sorted(checkpoint_dir.glob("checkpoint_*.nrs"))
            if not checkpoints:
                raise FileNotFoundError("No checkpoints found")

            checkpoint_file = checkpoints[checkpoint_index]
            session_data = self.load_from_file(checkpoint_file, decompress=True)

            self.logger.info(f"Restored from checkpoint: {checkpoint_file}")
            return session_data

        except Exception as e:
            self.logger.error(f"Restore error: {e}")
            raise


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    serializer = SessionSerializer()

    # Create sample session data
    session_data = {
        "nrs_version": "1.0",
        "session": {
            "id": "session_test_001",
            "name": "Test Session",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "mode": "offensive",
            "description": "Test session",
        },
        "conversation": {"messages": []},
        "task_state": {},
        "tools_state": {},
        "mode_state": {},
        "results": {},
        "metadata": {},
    }

    # Test serialization
    data = serializer.serialize(session_data)
    print(f"Serialized size: {len(data)} bytes")

    # Test compression
    compressed = serializer.serialize(session_data, compress=True)
    print(f"Compressed size: {len(compressed)} bytes")

    # Test deserialization
    restored = serializer.deserialize(data)
    print(f"Deserialized session: {restored['session']['name']}")
