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
                f"'{self.storage_path.parent}'. Please check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to create storage directory '{self.storage_path.parent}': {e}"
            ) from e

    def _create_backup(self) -> Optional[Path]:
        """Create a backup of the current storage file before saving.

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
                f"Please check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to create backup file '{backup_path}': {e}"
            ) from e

    def save(self, task_list: TaskList) -> None:
        """Save a task list to disk.

        Creates a backup of the existing file before saving.

        Raises:
            StorageError: If the file cannot be written due to permissions or other
                I/O errors.
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
                f"Please check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to save tasks to '{self.storage_path}': {e}"
            ) from e

    def load(self) -> Optional[TaskList]:
        """Load a task list from disk.

        Returns:
            The loaded TaskList, or None if the file doesn't exist.

        Raises:
            StorageError: If the file cannot be read due to permissions, corruption,
                or other I/O errors.
        """
        if not self.storage_path.exists():
            return None

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot read '{self.storage_path}'. "
                f"Please check your file permissions."
            ) from e
        except json.JSONDecodeError as e:
            raise StorageError(
                f"Corrupted data file: '{self.storage_path}' contains invalid JSON. "
                f"The file may be corrupted. Error: {e}. You may need to restore "
                f"from backup or delete the file to start fresh."
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
        except (KeyError, ValueError, TypeError) as e:
            raise StorageError(
                f"Corrupted data file: '{self.storage_path}' contains invalid task "
                f"data. Error: {e}. You may need to restore from backup or delete "
                f"the file to start fresh."
            ) from e

        return task_list

    def delete(self) -> bool:
        """Delete the storage file.

        Returns:
            True if deleted, False if not found.

        Raises:
            StorageError: If the file cannot be deleted due to permissions or other
                I/O errors.
        """
        if not self.storage_path.exists():
            return False

        try:
            os.remove(self.storage_path)
            return True
        except PermissionError as e:
            raise StorageError(
                f"Permission denied: Cannot delete '{self.storage_path}'. "
                f"Please check your file permissions."
            ) from e
        except OSError as e:
            raise StorageError(
                f"Failed to delete '{self.storage_path}': {e}"
            ) from e

    def exists(self) -> bool:
        """Check if storage file exists."""
        return self.storage_path.exists()


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
