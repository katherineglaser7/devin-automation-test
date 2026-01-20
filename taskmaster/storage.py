"""Storage backend for TaskMaster."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Task, TaskList


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class TaskStorage:
    """Handles persistence of tasks to disk."""

    DEFAULT_FILENAME = "tasks.json"
    BACKUP_SUFFIX = ".backup"

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize storage with optional custom path."""
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default to ~/.taskmaster/tasks.json
            self.storage_path = Path.home() / ".taskmaster" / self.DEFAULT_FILENAME

    def _ensure_directory(self) -> None:
        """Ensure the storage directory exists."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot create storage directory "
                f"'{self.storage_path.parent}'. Check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to create storage directory '{self.storage_path.parent}': {e}"
            ) from e

    def _create_backup(self) -> Optional[Path]:
        """Create a backup of the existing storage file before overwriting.

        Returns the backup path if a backup was created, None otherwise.
        """
        if not self.storage_path.exists():
            return None

        backup_path = self.storage_path.with_suffix(
            self.storage_path.suffix + self.BACKUP_SUFFIX
        )
        try:
            shutil.copy2(self.storage_path, backup_path)
            return backup_path
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot create backup file '{backup_path}'. "
                f"Check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to create backup file '{backup_path}': {e}"
            ) from e

    def save(self, task_list: TaskList) -> None:
        """Save a task list to disk.

        Creates a backup of the existing file before overwriting.
        Raises StorageError if the save operation fails.
        """
        self._ensure_directory()

        self._create_backup()

        data = {
            "name": task_list.name,
            "created_at": task_list.created_at.isoformat(),
            "tasks": [task.to_dict() for task in task_list.tasks],
        }

        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot write to '{self.storage_path}'. "
                f"Check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to save tasks to '{self.storage_path}': {e}"
            ) from e

    def load(self) -> Optional[TaskList]:
        """Load a task list from disk.

        Returns None if the storage file does not exist.
        Raises StorageError if the file cannot be read or contains invalid JSON.
        """
        if not self.storage_path.exists():
            return None

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot read '{self.storage_path}'. "
                f"Check your file permissions."
            ) from e
        except json.JSONDecodeError as e:
            raise StorageError(
                f"Corrupted data file: '{self.storage_path}' contains invalid JSON. "
                f"Error at line {e.lineno}, column {e.colno}: {e.msg}. "
                f"You may need to restore from backup or delete the file."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to read tasks from '{self.storage_path}': {e}"
            ) from e

        try:
            task_list = TaskList(
                name=data["name"],
                created_at=datetime.fromisoformat(data["created_at"]),
            )
            for task_data in data.get("tasks", []):
                task_list.add_task(Task.from_dict(task_data))
        except (KeyError, TypeError, ValueError) as e:
            raise StorageError(
                f"Corrupted data file: '{self.storage_path}' contains invalid "
                f"task data. Error: {e}. "
                f"You may need to restore from backup or delete the file."
            ) from e

        return task_list

    def delete(self) -> bool:
        """Delete the storage file. Returns True if deleted, False if not found.

        Raises StorageError if the file exists but cannot be deleted.
        """
        if not self.storage_path.exists():
            return False

        try:
            os.remove(self.storage_path)
            return True
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot delete '{self.storage_path}'. "
                f"Check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to delete storage file '{self.storage_path}': {e}"
            ) from e

    def exists(self) -> bool:
        """Check if storage file exists."""
        return self.storage_path.exists()

    def get_backup_path(self) -> Path:
        """Get the path to the backup file."""
        return self.storage_path.with_suffix(
            self.storage_path.suffix + self.BACKUP_SUFFIX
        )

    def restore_from_backup(self) -> bool:
        """Restore the storage file from backup.

        Returns True if restored successfully, False if no backup exists.
        Raises StorageError if the restore operation fails.
        """
        backup_path = self.get_backup_path()
        if not backup_path.exists():
            return False

        try:
            shutil.copy2(backup_path, self.storage_path)
            return True
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot restore from backup '{backup_path}'. "
                f"Check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to restore from backup '{backup_path}': {e}"
            ) from e


class TaskManager:
    """High-level interface for managing tasks."""

    def __init__(self, storage: Optional[TaskStorage] = None):
        """Initialize the task manager."""
        self.storage = storage or TaskStorage()
        self._task_list: Optional[TaskList] = None

    @property
    def task_list(self) -> TaskList:
        """Get or create the task list."""
        if self._task_list is None:
            self._task_list = self.storage.load()
            if self._task_list is None:
                self._task_list = TaskList(name="My Tasks")
        return self._task_list

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: list[str] = None,
    ) -> Task:
        """Add a new task."""
        from .models import Priority

        task = Task(
            title=title,
            description=description,
            priority=Priority(priority),
            tags=tags or [],
        )
        self.task_list.add_task(task)
        self.storage.save(self.task_list)
        return task

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as complete."""
        task = self.task_list.get_task(task_id)
        if task:
            task.mark_complete()
            self.storage.save(self.task_list)
        return task

    def delete_task(self, task_id: str) -> Optional[Task]:
        """Delete a task by ID."""
        task = self.task_list.remove_task(task_id)
        if task:
            self.storage.save(self.task_list)
        return task

    def list_tasks(self, status: str = None, priority: str = None) -> list[Task]:
        """List tasks with optional filtering."""
        tasks = self.task_list.tasks

        if status:
            from .models import Status

            tasks = [t for t in tasks if t.status == Status(status)]

        if priority:
            from .models import Priority

            tasks = [t for t in tasks if t.priority == Priority(priority)]

        return tasks

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID."""
        return self.task_list.get_task(task_id)

    def clear_completed(self) -> int:
        """Remove all completed tasks. Returns count of removed tasks."""
        from .models import Status

        completed = [t for t in self.task_list.tasks if t.status == Status.COMPLETED]
        for task in completed:
            self.task_list.remove_task(task.id)
        self.storage.save(self.task_list)
        return len(completed)
