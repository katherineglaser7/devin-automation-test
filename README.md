# TaskMaster

A simple command-line task management tool built with Python.

## Description

TaskMaster is a CLI application for managing tasks directly from your terminal. It provides a lightweight, file-based task management system with support for priorities, statuses, and tags. Built with Click for command parsing and Rich for beautiful terminal output, TaskMaster stores all your tasks locally in JSON format at `~/.taskmaster/tasks.json`.

## Installation

### Prerequisites

TaskMaster requires Python 3.8 or higher.

### Install from Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/katherineglaser7/devin-automation-test.git
cd devin-automation-test
pip install -e .
```

### Install with Development Dependencies

To install with development tools (pytest, black, ruff):

```bash
pip install -e ".[dev]"
```

## Usage

### Adding Tasks

Create a new task with a title:

```bash
taskmaster add "My first task"
```

Add a task with priority, description, and tags:

```bash
taskmaster add "Important task" --priority high --description "This needs to be done soon" --tag work --tag urgent
```

Priority levels: `low`, `medium` (default), `high`, `critical`

### Listing Tasks

List all tasks:

```bash
taskmaster list
```

Filter tasks by status:

```bash
taskmaster list --status pending
taskmaster list --status completed
```

Filter tasks by priority:

```bash
taskmaster list --priority high
taskmaster list --priority critical
```

### Viewing Task Details

Show detailed information about a specific task:

```bash
taskmaster show <task_id>
```

### Completing Tasks

Mark a task as complete:

```bash
taskmaster complete <task_id>
```

### Deleting Tasks

Delete a specific task:

```bash
taskmaster delete <task_id>
```

Remove all completed tasks:

```bash
taskmaster clear
```

### Getting Help

View available commands:

```bash
taskmaster --help
```

Get help for a specific command:

```bash
taskmaster add --help
```

## Features

TaskMaster supports the following features:

- Create, list, complete, and delete tasks
- Four priority levels (low, medium, high, critical)
- Status tracking (pending, in_progress, completed, cancelled)
- Tag support for organizing tasks
- Persistent local storage in JSON format
- Color-coded terminal output for better readability
- Filtering tasks by status or priority

## Contributing

Contributions are welcome! Here's how you can help:

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/devin-automation-test.git
   cd devin-automation-test
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Code Style

This project uses Black for code formatting and Ruff for linting. Before submitting changes, ensure your code passes all checks:

```bash
black taskmaster/ tests/
ruff check taskmaster/ tests/
```

### Running Tests

Run the test suite with pytest:

```bash
pytest tests/
```

Run tests with coverage report:

```bash
pytest --cov=taskmaster tests/
```

### Submitting Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit them with clear, descriptive messages
3. Push your branch and open a pull request
4. Ensure all CI checks pass

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with a clear description of the problem or suggestion.

## License

This project is licensed under the MIT License.      
