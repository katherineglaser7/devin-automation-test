"""Command-line interface for TaskMaster."""

import click
from rich.console import Console
from rich.table import Table

from .models import Priority, Status
from .storage import TaskManager

console = Console()


def get_priority_color(priority: Priority) -> str:
    """Get color for priority level."""
    colors = {
        Priority.LOW: "dim",
        Priority.MEDIUM: "blue",
        Priority.HIGH: "yellow",
        Priority.CRITICAL: "red bold",
    }
    return colors.get(priority, "white")


def get_status_color(status: Status) -> str:
    """Get color for status."""
    colors = {
        Status.PENDING: "white",
        Status.IN_PROGRESS: "cyan",
        Status.COMPLETED: "green",
        Status.CANCELLED: "dim",
    }
    return colors.get(status, "white")


@click.group()
@click.version_option()
def main():
    """TaskMaster - A simple command-line task management tool."""
    pass


@main.command()
@click.argument("title")
@click.option("-d", "--description", default="", help="Task description")
@click.option(
    "-p", "--priority",
    type=click.Choice(["low", "medium", "high", "critical"]),
    default="medium",
    help="Task priority"
)
@click.option("-t", "--tag", multiple=True, help="Add tags to the task")
def add(title: str, description: str, priority: str, tag: tuple):
    """Add a new task."""
    manager = TaskManager()
    task = manager.add_task(
        title=title,
        description=description,
        priority=priority,
        tags=list(tag),
    )
    console.print(f"[green]Created task:[/green] {task.title} [dim](ID: {task.id})[/dim]")


@main.command()
@click.option(
    "-s", "--status",
    type=click.Choice(["pending", "in_progress", "completed", "cancelled"]),
    help="Filter by status"
)
@click.option(
    "-p", "--priority",
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Filter by priority"
)
@click.option(
    "-t", "--tag",
    multiple=True,
    help="Filter by tag (can be specified multiple times, case-insensitive)"
)
@click.option(
    "--match-any",
    is_flag=True,
    default=False,
    help="Match tasks with ANY of the specified tags (default: match ALL tags)"
)
def list(status: str, priority: str, tag: tuple, match_any: bool):
    """List all tasks."""
    manager = TaskManager()
    tasks = manager.list_tasks(
        status=status,
        priority=priority,
        tags=list(tag) if tag else None,
        match_all_tags=not match_any,
    )

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    table = Table(title="Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Priority")
    table.add_column("Status")
    table.add_column("Tags")

    for task in tasks:
        priority_style = get_priority_color(task.priority)
        status_style = get_status_color(task.status)
        tags_str = ", ".join(task.tags) if task.tags else "-"

        table.add_row(
            task.id,
            task.title,
            f"[{priority_style}]{task.priority.value}[/{priority_style}]",
            f"[{status_style}]{task.status.value}[/{status_style}]",
            tags_str,
        )

    console.print(table)


@main.command()
@click.argument("task_id")
def complete(task_id: str):
    """Mark a task as complete."""
    manager = TaskManager()
    task = manager.complete_task(task_id)
    if task:
        console.print(f"[green]Completed:[/green] {task.title}")
    else:
        console.print(f"[red]Task not found:[/red] {task_id}")


@main.command()
@click.argument("task_id")
def delete(task_id: str):
    """Delete a task."""
    manager = TaskManager()
    task = manager.delete_task(task_id)
    if task:
        console.print(f"[yellow]Deleted:[/yellow] {task.title}")
    else:
        console.print(f"[red]Task not found:[/red] {task_id}")


@main.command()
@click.argument("task_id")
def show(task_id: str):
    """Show details of a specific task."""
    manager = TaskManager()
    task = manager.get_task(task_id)

    if not task:
        console.print(f"[red]Task not found:[/red] {task_id}")
        return

    console.print(f"\n[bold]{task.title}[/bold]")
    console.print(f"[dim]ID: {task.id}[/dim]")
    console.print(f"Description: {task.description or '(none)'}")
    console.print(f"Priority: [{get_priority_color(task.priority)}]{task.priority.value}[/{get_priority_color(task.priority)}]")
    console.print(f"Status: [{get_status_color(task.status)}]{task.status.value}[/{get_status_color(task.status)}]")
    console.print(f"Tags: {', '.join(task.tags) if task.tags else '(none)'}")
    console.print(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M')}")


@main.command()
def clear():
    """Remove all completed tasks."""
    manager = TaskManager()
    count = manager.clear_completed()
    if count > 0:
        console.print(f"[green]Cleared {count} completed task(s).[/green]")
    else:
        console.print("[dim]No completed tasks to clear.[/dim]")


if __name__ == "__main__":
    main()
