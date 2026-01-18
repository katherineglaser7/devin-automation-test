"""Tests for TaskMaster models."""

import pytest
from datetime import datetime

from taskmaster.models import Task, TaskList, Priority, Status


class TestTask:
    """Tests for the Task model."""

    def test_create_task_with_defaults(self):
        """Test creating a task with default values."""
        task = Task(title="Test task")
        assert task.title == "Test task"
        assert task.description == ""
        assert task.priority == Priority.MEDIUM
        assert task.status == Status.PENDING
        assert task.tags == []
        assert task.id is not None

    def test_create_task_with_all_fields(self):
        """Test creating a task with all fields specified."""
        task = Task(
            title="Complete task",
            description="A detailed description",
            priority=Priority.HIGH,
            tags=["work", "urgent"],
        )
        assert task.title == "Complete task"
        assert task.description == "A detailed description"
        assert task.priority == Priority.HIGH
        assert task.tags == ["work", "urgent"]

    def test_mark_complete(self):
        """Test marking a task as complete."""
        task = Task(title="Test task")
        original_updated = task.updated_at
        task.mark_complete()
        assert task.status == Status.COMPLETED
        assert task.updated_at >= original_updated

    def test_mark_in_progress(self):
        """Test marking a task as in progress."""
        task = Task(title="Test task")
        task.mark_in_progress()
        assert task.status == Status.IN_PROGRESS

    def test_to_dict(self):
        """Test converting task to dictionary."""
        task = Task(title="Test task", description="Description")
        data = task.to_dict()
        assert data["title"] == "Test task"
        assert data["description"] == "Description"
        assert data["priority"] == "medium"
        assert data["status"] == "pending"

    def test_from_dict(self):
        """Test creating task from dictionary."""
        data = {
            "id": "abc123",
            "title": "Test task",
            "description": "Description",
            "priority": "high",
            "status": "in_progress",
            "tags": ["test"],
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T11:00:00",
        }
        task = Task.from_dict(data)
        assert task.id == "abc123"
        assert task.title == "Test task"
        assert task.priority == Priority.HIGH
        assert task.status == Status.IN_PROGRESS


class TestTaskList:
    """Tests for the TaskList model."""

    def test_create_empty_task_list(self):
        """Test creating an empty task list."""
        task_list = TaskList(name="My Tasks")
        assert task_list.name == "My Tasks"
        assert task_list.tasks == []

    def test_add_task(self):
        """Test adding a task to the list."""
        task_list = TaskList(name="My Tasks")
        task = Task(title="Test task")
        task_list.add_task(task)
        assert len(task_list.tasks) == 1
        assert task_list.tasks[0] == task

    def test_remove_task(self):
        """Test removing a task from the list."""
        task_list = TaskList(name="My Tasks")
        task = Task(title="Test task")
        task_list.add_task(task)
        removed = task_list.remove_task(task.id)
        assert removed == task
        assert len(task_list.tasks) == 0

    def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        task_list = TaskList(name="My Tasks")
        removed = task_list.remove_task("nonexistent")
        assert removed is None

    def test_get_task(self):
        """Test getting a task by ID."""
        task_list = TaskList(name="My Tasks")
        task = Task(title="Test task")
        task_list.add_task(task)
        found = task_list.get_task(task.id)
        assert found == task

    def test_get_tasks_by_status(self):
        """Test filtering tasks by status."""
        task_list = TaskList(name="My Tasks")
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")
        task2.mark_complete()
        task_list.add_task(task1)
        task_list.add_task(task2)

        pending = task_list.get_tasks_by_status(Status.PENDING)
        completed = task_list.get_tasks_by_status(Status.COMPLETED)

        assert len(pending) == 1
        assert len(completed) == 1
        assert pending[0] == task1
        assert completed[0] == task2

    def test_get_tasks_by_priority(self):
        """Test filtering tasks by priority."""
        task_list = TaskList(name="My Tasks")
        task1 = Task(title="Task 1", priority=Priority.LOW)
        task2 = Task(title="Task 2", priority=Priority.HIGH)
        task_list.add_task(task1)
        task_list.add_task(task2)

        high_priority = task_list.get_tasks_by_priority(Priority.HIGH)
        assert len(high_priority) == 1
        assert high_priority[0] == task2
