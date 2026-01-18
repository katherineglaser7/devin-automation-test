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
@click.option("--due", default=None, help="Due date (YYYY-MM-DD format)")
def add(title: str, description: str, priority: str, tag: tuple, due: str):
    """Add a new task."""
    manager = TaskManager()
    task = manager.add_task(
        title=title,
        description=description,
        priority=priority,
        tags=list(tag),
        due_date=due,
    )
    due_str = ""
    if task.due_date:
        due_str = f" [dim](Due: {task.due_date.strftime('%Y-%m-%d')})[/dim]"
    msg = f"[green]Created task:[/green] {task.title} [dim](ID: {task.id})[/dim]"
    console.print(f"{msg}{due_str}")


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
def list(status: str, priority: str):
    """List all tasks."""
    manager = TaskManager()
    tasks = manager.list_tasks(status=status, priority=priority)

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    table = Table(title="Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Priority")
    table.add_column("Status")
    table.add_column("Due Date")
    table.add_column("Tags")

    for task in tasks:
        priority_style = get_priority_color(task.priority)
        status_style = get_status_color(task.status)
        tags_str = ", ".join(task.tags) if task.tags else "-"

        if task.due_date:
            due_str = task.due_date.strftime("%Y-%m-%d")
            if task.is_overdue:
                due_str = f"[red bold]{due_str}[/red bold]"
        else:
            due_str = "-"

        table.add_row(
            task.id,
            task.title,
            f"[{priority_style}]{task.priority.value}[/{priority_style}]",
            f"[{status_style}]{task.status.value}[/{status_style}]",
            due_str,
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
    p_color = get_priority_color(task.priority)
    console.print(f"Priority: [{p_color}]{task.priority.value}[/{p_color}]")
    s_color = get_status_color(task.status)
    console.print(f"Status: [{s_color}]{task.status.value}[/{s_color}]")
    if task.due_date:
        due_style = "red bold" if task.is_overdue else "white"
        due_fmt = task.due_date.strftime('%Y-%m-%d %H:%M')
        console.print(f"Due Date: [{due_style}]{due_fmt}[/{due_style}]")
    else:
        console.print("Due Date: (none)")
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
