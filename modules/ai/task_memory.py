#!/usr/bin/env python3
"""
NeuroRift Task Memory
Persistent task state storage and management.

Contributors:
- NeuroRift Core Team
- x1xhlol (system-prompts-and-models-of-ai-tools)
- SimStudioAI (conceptual orchestration)
- Anti-Gravity AI
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class TaskMemory:
    """
    Manages persistent storage of task state for NeuroRift.

    Provides checkpoint/resume capability and execution history tracking.
    """

    def __init__(self, storage_path: str = "~/.neurorift/task_memory"):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.current_task: Optional[Dict] = None

        self.logger.info(f"Task memory initialized at: {self.storage_path}")

    def create_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """
        Create a new task in memory.

        Args:
            task_id: Unique task identifier
            task_data: Task data to store
        """
        task_data["task_id"] = task_id
        task_data["created_at"] = datetime.now().isoformat()
        task_data["updated_at"] = datetime.now().isoformat()
        task_data["checkpoints"] = []

        self.current_task = task_data
        self._save_task(task_id, task_data)

        self.logger.info(f"Task created: {task_id}")

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> None:
        """
        Update an existing task.

        Args:
            task_id: Task identifier
            updates: Dictionary of updates to apply
        """
        task_data = self.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task not found: {task_id}")

        task_data.update(updates)
        task_data["updated_at"] = datetime.now().isoformat()

        self.current_task = task_data
        self._save_task(task_id, task_data)

        self.logger.debug(f"Task updated: {task_id}")

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task from memory.

        Args:
            task_id: Task identifier

        Returns:
            Task data or None if not found
        """
        task_file = self.storage_path / f"{task_id}.json"

        if not task_file.exists():
            return None

        try:
            with open(task_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading task {task_id}: {e}")
            return None

    def checkpoint(self, task_id: str, checkpoint_data: Dict[str, Any]) -> None:
        """
        Create a checkpoint for a task.

        Args:
            task_id: Task identifier
            checkpoint_data: Checkpoint data to store
        """
        task_data = self.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task not found: {task_id}")

        checkpoint = {"timestamp": datetime.now().isoformat(), "data": checkpoint_data}

        task_data.setdefault("checkpoints", []).append(checkpoint)
        self._save_task(task_id, task_data)

        self.logger.info(f"Checkpoint created for task: {task_id}")

    def get_latest_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest checkpoint for a task.

        Args:
            task_id: Task identifier

        Returns:
            Latest checkpoint data or None
        """
        task_data = self.get_task(task_id)
        if not task_data:
            return None

        checkpoints = task_data.get("checkpoints", [])
        if not checkpoints:
            return None

        return checkpoints[-1]["data"]

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all tasks, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            List of task summaries
        """
        tasks = []

        for task_file in self.storage_path.glob("task_*.json"):
            try:
                with open(task_file, "r") as f:
                    task_data = json.load(f)

                if status is None or task_data.get("status") == status:
                    tasks.append(
                        {
                            "task_id": task_data.get("task_id"),
                            "status": task_data.get("status"),
                            "mode": task_data.get("mode"),
                            "target": task_data.get("target"),
                            "created_at": task_data.get("created_at"),
                            "updated_at": task_data.get("updated_at"),
                        }
                    )
            except Exception as e:
                self.logger.error(f"Error reading task file {task_file}: {e}")

        return sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task from memory.

        Args:
            task_id: Task identifier

        Returns:
            True if deleted, False if not found
        """
        task_file = self.storage_path / f"{task_id}.json"

        if not task_file.exists():
            return False

        try:
            task_file.unlink()
            self.logger.info(f"Task deleted: {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting task {task_id}: {e}")
            return False

    def _save_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """Save task data to file"""
        task_file = self.storage_path / f"{task_id}.json"

        try:
            with open(task_file, "w") as f:
                json.dump(task_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving task {task_id}: {e}")
            raise

    def get_history(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get execution history for a task.

        Args:
            task_id: Task identifier
            limit: Maximum number of history entries

        Returns:
            List of history entries
        """
        task_data = self.get_task(task_id)
        if not task_data:
            return []

        history = task_data.get("history", [])
        return history[-limit:]

    def add_history_entry(self, task_id: str, entry: Dict[str, Any]) -> None:
        """
        Add an entry to task history.

        Args:
            task_id: Task identifier
            entry: History entry to add
        """
        task_data = self.get_task(task_id)
        if not task_data:
            raise ValueError(f"Task not found: {task_id}")

        entry["timestamp"] = datetime.now().isoformat()
        task_data.setdefault("history", []).append(entry)

        # Limit history size
        max_history = 100
        if len(task_data["history"]) > max_history:
            task_data["history"] = task_data["history"][-max_history:]

        self._save_task(task_id, task_data)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize task memory
    memory = TaskMemory()

    # Create a task
    task_id = "task_20260124_092347"
    memory.create_task(
        task_id,
        {
            "user_request": "Scan example.com",
            "mode": "offensive",
            "target": "example.com",
            "status": "initialized",
        },
    )

    # Update task
    memory.update_task(task_id, {"status": "planning"})

    # Create checkpoint
    memory.checkpoint(task_id, {"agent": "planner", "output": {"plan_id": "plan_001"}})

    # List tasks
    tasks = memory.list_tasks()
    print(f"\nTasks: {len(tasks)}")
    for task in tasks:
        print(f"  - {task['task_id']}: {task['status']}")
