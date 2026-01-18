"""Storage backend for TaskMaster."""

import json
import os
from pathlib import Path
from typing import Optional

from .models import Task, TaskList


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class TaskStorage:
    """Handles persistence of tasks to disk."""

    DEFAULT_FILENAME = "tasks.json"

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize storage with optional custom path."""
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default to ~/.taskmaster/tasks.json
            self.storage_path = Path.home() / ".taskmaster" / self.DEFAULT_FILENAME

    def _ensure_directory(self) -> None:
        """Ensure the storage directory exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, task_list: TaskList) -> None:
        """Save a task list to disk."""
        self._ensure_directory()
        data = {
            "name": task_list.name,
            "created_at": task_list.created_at.isoformat(),
            "tasks": [task.to_dict() for task in task_list.tasks],
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> Optional[TaskList]:
        """Load a task list from disk."""
        if not self.storage_path.exists():
            return None

        with open(self.storage_path, "r") as f:
            data = json.load(f)

        from datetime import datetime
        task_list = TaskList(
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
        for task_data in data.get("tasks", []):
            task_list.add_task(Task.from_dict(task_data))

        return task_list

    def delete(self) -> bool:
        """Delete the storage file. Returns True if deleted, False if not found."""
        if self.storage_path.exists():
            os.remove(self.storage_path)
            return True
        return False

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

    def add_task(self, title: str, description: str = "", priority: str = "medium", tags: list[str] = None) -> Task:
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
