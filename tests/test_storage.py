"""Tests for TaskMaster storage module."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from taskmaster.models import Priority, Status, Task, TaskList
from taskmaster.storage import StorageError, TaskManager, TaskStorage


class TestTaskStorage:
    """Tests for the TaskStorage class."""

    def test_init_with_default_path(self):
        """Test TaskStorage initializes with default path."""
        storage = TaskStorage()
        expected_path = Path.home() / ".taskmaster" / "tasks.json"
        assert storage.storage_path == expected_path

    def test_init_with_custom_path(self):
        """Test TaskStorage initializes with custom path."""
        custom_path = "/tmp/custom/tasks.json"
        storage = TaskStorage(storage_path=custom_path)
        assert storage.storage_path == Path(custom_path)

    def test_save_creates_directory(self):
        """Test save creates parent directory if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "subdir", "tasks.json")
            storage = TaskStorage(storage_path=storage_path)
            task_list = TaskList(name="Test List")

            storage.save(task_list)

            assert os.path.exists(storage_path)
            assert os.path.isdir(os.path.join(tmpdir, "subdir"))

    def test_save_and_load_empty_task_list(self):
        """Test saving and loading an empty task list."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "tasks.json")
            storage = TaskStorage(storage_path=storage_path)
            task_list = TaskList(name="Empty List")

            storage.save(task_list)
            loaded = storage.load()

            assert loaded is not None
            assert loaded.name == "Empty List"
            assert len(loaded.tasks) == 0

    def test_save_and_load_task_list_with_tasks(self):
        """Test saving and loading a task list with tasks."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "tasks.json")
            storage = TaskStorage(storage_path=storage_path)

            task_list = TaskList(name="My Tasks")
            task1 = Task(title="Task 1", priority=Priority.HIGH)
            task2 = Task(title="Task 2", description="Description", tags=["work"])
            task_list.add_task(task1)
            task_list.add_task(task2)

            storage.save(task_list)
            loaded = storage.load()

            assert loaded is not None
            assert loaded.name == "My Tasks"
            assert len(loaded.tasks) == 2
            assert loaded.tasks[0].title == "Task 1"
            assert loaded.tasks[0].priority == Priority.HIGH
            assert loaded.tasks[1].title == "Task 2"
            assert loaded.tasks[1].description == "Description"
            assert loaded.tasks[1].tags == ["work"]

    def test_load_nonexistent_file(self):
        """Test loading from a file that doesn't exist returns None."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "nonexistent.json")
            storage = TaskStorage(storage_path=storage_path)

            result = storage.load()

            assert result is None

    def test_delete_existing_file(self):
        """Test deleting an existing storage file."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "tasks.json")
            storage = TaskStorage(storage_path=storage_path)
            task_list = TaskList(name="Test")
            storage.save(task_list)

            assert os.path.exists(storage_path)
            result = storage.delete()

            assert result is True
            assert not os.path.exists(storage_path)

    def test_delete_nonexistent_file(self):
        """Test deleting a file that doesn't exist returns False."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "nonexistent.json")
            storage = TaskStorage(storage_path=storage_path)

            result = storage.delete()

            assert result is False

    def test_exists_when_file_exists(self):
        """Test exists returns True when file exists."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "tasks.json")
            storage = TaskStorage(storage_path=storage_path)
            task_list = TaskList(name="Test")
            storage.save(task_list)

            assert storage.exists() is True

    def test_exists_when_file_does_not_exist(self):
        """Test exists returns False when file doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "nonexistent.json")
            storage = TaskStorage(storage_path=storage_path)

            assert storage.exists() is False

    def test_save_preserves_task_data(self):
        """Test that save preserves all task data correctly."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "tasks.json")
            storage = TaskStorage(storage_path=storage_path)

            task = Task(
                title="Complete Task",
                description="Full description",
                priority=Priority.CRITICAL,
                tags=["urgent", "important"],
            )
            task.mark_complete()
            task_list = TaskList(name="Test List")
            task_list.add_task(task)

            storage.save(task_list)
            loaded = storage.load()

            loaded_task = loaded.tasks[0]
            assert loaded_task.title == "Complete Task"
            assert loaded_task.description == "Full description"
            assert loaded_task.priority == Priority.CRITICAL
            assert loaded_task.status == Status.COMPLETED
            assert loaded_task.tags == ["urgent", "important"]
            assert loaded_task.id == task.id


class TestTaskManager:
    """Tests for the TaskManager class."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage for testing."""
        with TemporaryDirectory() as tmpdir:
            storage_path = os.path.join(tmpdir, "tasks.json")
            storage = TaskStorage(storage_path=storage_path)
            yield storage

    @pytest.fixture
    def manager(self, temp_storage):
        """Create a TaskManager with temporary storage."""
        return TaskManager(storage=temp_storage)

    def test_init_with_default_storage(self):
        """Test TaskManager initializes with default storage."""
        manager = TaskManager()
        assert manager.storage is not None
        assert isinstance(manager.storage, TaskStorage)

    def test_init_with_custom_storage(self, temp_storage):
        """Test TaskManager initializes with custom storage."""
        manager = TaskManager(storage=temp_storage)
        assert manager.storage == temp_storage

    def test_task_list_creates_new_if_not_exists(self, manager):
        """Test task_list property creates new TaskList if none exists."""
        task_list = manager.task_list
        assert task_list is not None
        assert task_list.name == "My Tasks"
        assert len(task_list.tasks) == 0

    def test_task_list_loads_existing(self, temp_storage):
        """Test task_list property loads existing TaskList."""
        existing_list = TaskList(name="Existing List")
        existing_list.add_task(Task(title="Existing Task"))
        temp_storage.save(existing_list)

        manager = TaskManager(storage=temp_storage)
        task_list = manager.task_list

        assert task_list.name == "Existing List"
        assert len(task_list.tasks) == 1
        assert task_list.tasks[0].title == "Existing Task"

    def test_task_list_lazy_loading(self, manager):
        """Test task_list is lazily loaded."""
        assert manager._task_list is None
        _ = manager.task_list
        assert manager._task_list is not None

    def test_add_task_with_defaults(self, manager):
        """Test adding a task with default values."""
        task = manager.add_task(title="New Task")

        assert task.title == "New Task"
        assert task.description == ""
        assert task.priority == Priority.MEDIUM
        assert task.status == Status.PENDING
        assert task.tags == []
        assert len(manager.task_list.tasks) == 1

    def test_add_task_with_all_parameters(self, manager):
        """Test adding a task with all parameters specified."""
        task = manager.add_task(
            title="Full Task",
            description="A detailed description",
            priority="high",
            tags=["work", "urgent"],
        )

        assert task.title == "Full Task"
        assert task.description == "A detailed description"
        assert task.priority == Priority.HIGH
        assert task.tags == ["work", "urgent"]

    def test_add_task_persists_to_storage(self, manager, temp_storage):
        """Test that adding a task persists it to storage."""
        manager.add_task(title="Persisted Task")

        loaded = temp_storage.load()
        assert len(loaded.tasks) == 1
        assert loaded.tasks[0].title == "Persisted Task"

    def test_add_multiple_tasks(self, manager):
        """Test adding multiple tasks."""
        manager.add_task(title="Task 1")
        manager.add_task(title="Task 2")
        manager.add_task(title="Task 3")

        assert len(manager.task_list.tasks) == 3

    def test_complete_task_success(self, manager):
        """Test completing an existing task."""
        task = manager.add_task(title="Task to Complete")
        task_id = task.id

        result = manager.complete_task(task_id)

        assert result is not None
        assert result.status == Status.COMPLETED
        assert manager.task_list.get_task(task_id).status == Status.COMPLETED

    def test_complete_task_nonexistent(self, manager):
        """Test completing a task that doesn't exist."""
        result = manager.complete_task("nonexistent-id")
        assert result is None

    def test_complete_task_persists(self, manager, temp_storage):
        """Test that completing a task persists the change."""
        task = manager.add_task(title="Task to Complete")
        manager.complete_task(task.id)

        loaded = temp_storage.load()
        assert loaded.tasks[0].status == Status.COMPLETED

    def test_delete_task_success(self, manager):
        """Test deleting an existing task."""
        task = manager.add_task(title="Task to Delete")
        task_id = task.id

        result = manager.delete_task(task_id)

        assert result is not None
        assert result.id == task_id
        assert len(manager.task_list.tasks) == 0

    def test_delete_task_nonexistent(self, manager):
        """Test deleting a task that doesn't exist."""
        result = manager.delete_task("nonexistent-id")
        assert result is None

    def test_delete_task_persists(self, manager, temp_storage):
        """Test that deleting a task persists the change."""
        task = manager.add_task(title="Task to Delete")
        manager.delete_task(task.id)

        loaded = temp_storage.load()
        assert len(loaded.tasks) == 0

    def test_list_tasks_no_filter(self, manager):
        """Test listing all tasks without filters."""
        manager.add_task(title="Task 1")
        manager.add_task(title="Task 2")
        manager.add_task(title="Task 3")

        tasks = manager.list_tasks()

        assert len(tasks) == 3

    def test_list_tasks_filter_by_status(self, manager):
        """Test listing tasks filtered by status."""
        manager.add_task(title="Pending Task")
        completed_task = manager.add_task(title="Completed Task")
        manager.complete_task(completed_task.id)

        pending_tasks = manager.list_tasks(status="pending")
        completed_tasks = manager.list_tasks(status="completed")

        assert len(pending_tasks) == 1
        assert pending_tasks[0].title == "Pending Task"
        assert len(completed_tasks) == 1
        assert completed_tasks[0].title == "Completed Task"

    def test_list_tasks_filter_by_priority(self, manager):
        """Test listing tasks filtered by priority."""
        manager.add_task(title="Low Priority", priority="low")
        manager.add_task(title="High Priority", priority="high")
        manager.add_task(title="Medium Priority", priority="medium")

        high_tasks = manager.list_tasks(priority="high")
        low_tasks = manager.list_tasks(priority="low")

        assert len(high_tasks) == 1
        assert high_tasks[0].title == "High Priority"
        assert len(low_tasks) == 1
        assert low_tasks[0].title == "Low Priority"

    def test_list_tasks_filter_by_status_and_priority(self, manager):
        """Test listing tasks filtered by both status and priority."""
        manager.add_task(title="High Pending", priority="high")
        high_completed = manager.add_task(title="High Completed", priority="high")
        manager.add_task(title="Low Pending", priority="low")
        manager.complete_task(high_completed.id)

        tasks = manager.list_tasks(status="pending", priority="high")

        assert len(tasks) == 1
        assert tasks[0].title == "High Pending"

    def test_list_tasks_empty(self, manager):
        """Test listing tasks when there are none."""
        tasks = manager.list_tasks()
        assert len(tasks) == 0

    def test_get_task_success(self, manager):
        """Test getting an existing task by ID."""
        task = manager.add_task(title="Task to Get")

        result = manager.get_task(task.id)

        assert result is not None
        assert result.id == task.id
        assert result.title == "Task to Get"

    def test_get_task_nonexistent(self, manager):
        """Test getting a task that doesn't exist."""
        result = manager.get_task("nonexistent-id")
        assert result is None

    def test_clear_completed_removes_completed_tasks(self, manager):
        """Test that clear_completed removes all completed tasks."""
        manager.add_task(title="Pending Task")
        completed1 = manager.add_task(title="Completed Task 1")
        completed2 = manager.add_task(title="Completed Task 2")
        manager.complete_task(completed1.id)
        manager.complete_task(completed2.id)

        count = manager.clear_completed()

        assert count == 2
        assert len(manager.task_list.tasks) == 1
        assert manager.task_list.tasks[0].title == "Pending Task"

    def test_clear_completed_returns_zero_when_none_completed(self, manager):
        """Test clear_completed returns 0 when no tasks are completed."""
        manager.add_task(title="Pending Task 1")
        manager.add_task(title="Pending Task 2")

        count = manager.clear_completed()

        assert count == 0
        assert len(manager.task_list.tasks) == 2

    def test_clear_completed_persists(self, manager, temp_storage):
        """Test that clear_completed persists the changes."""
        task = manager.add_task(title="Completed Task")
        manager.complete_task(task.id)
        manager.clear_completed()

        loaded = temp_storage.load()
        assert len(loaded.tasks) == 0

    def test_clear_completed_empty_list(self, manager):
        """Test clear_completed on an empty task list."""
        count = manager.clear_completed()
        assert count == 0


class TestStorageError:
    """Tests for the StorageError exception."""

    def test_storage_error_is_exception(self):
        """Test that StorageError is an Exception."""
        error = StorageError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
