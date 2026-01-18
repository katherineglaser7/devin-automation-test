"""Data models for TaskMaster."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Priority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(Enum):
    """Task status options."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task in the system."""
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.status = Status.COMPLETED
        self.updated_at = datetime.now()

    def mark_in_progress(self) -> None:
        """Mark the task as in progress."""
        self.status = Status.IN_PROGRESS
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert task to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create a Task from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            priority=Priority(data.get("priority", "medium")),
            status=Status(data.get("status", "pending")),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class TaskList:
    """A collection of tasks."""
    name: str
    tasks: list[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: Task) -> None:
        """Add a task to the list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> Optional[Task]:
        """Remove a task by ID. Returns the removed task or None."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                return self.tasks.pop(i)
        return None

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_status(self, status: Status) -> list[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks if task.status == status]

    def get_tasks_by_priority(self, priority: Priority) -> list[Task]:
        """Get all tasks with a specific priority."""
        return [task for task in self.tasks if task.priority == priority]
