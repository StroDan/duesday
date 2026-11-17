"""Command-line entry point. The only module that reads the clock or prints."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.text import Text

from . import render
from .storage import StorageError, default_path, load_tasks, save_tasks
from .tasks import TaskError, add_task, mark_done, parse_due, sort_tasks


def build_parser() -> argparse.ArgumentParser:
    # --file is accepted before or after the command name. The sub-command copy
    # uses SUPPRESS so it only overrides the top-level value when given.
    file_help = "task file to use (default: ~/.duesday/tasks.json)"
    sub_common = argparse.ArgumentParser(add_help=False)
    sub_common.add_argument("--file", default=argparse.SUPPRESS, help=file_help)

    parser = argparse.ArgumentParser(prog="plan", description="Keep all your deadlines in one place.")
    parser.add_argument("--file", default=None, help=file_help)
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p_add = sub.add_parser("add", parents=[sub_common], help="add a task")
    p_add.add_argument("title")
    p_add.add_argument("--due", metavar="YYYY-MM-DD", help="due date")

    sub.add_parser("list", parents=[sub_common], help="list tasks by urgency")

    p_done = sub.add_parser("done", parents=[sub_common], help="mark a task done")
    p_done.add_argument("number", type=int)

    sub.add_parser("month", parents=[sub_common], help="show this month's calendar")
    return parser


def main(argv: list[str] | None = None, today: date | None = None, console: Console | None = None) -> int:
    args = build_parser().parse_args(argv)
    today = today or date.today()
    console = console or Console()
    path = Path(args.file) if args.file else default_path()

    def say(text: str, style: str = "") -> None:
        console.print(Text(text, style=style))

    try:
        tasks = load_tasks(path)

        if args.command == "add":
            due = parse_due(args.due) if args.due is not None else None
            task = add_task(tasks, args.title, due)
            save_tasks(path, tasks)
            msg = f"Added task #{task.id}: {task.title}"
            say(msg + (f" (due {task.due.isoformat()})" if task.due else ""), "green")

        elif args.command == "list":
            if not tasks:
                say("No tasks yet.")
            else:
                console.print(render.task_table(sort_tasks(tasks, today), today))

        elif args.command == "done":
            task, changed = mark_done(tasks, args.number)
            if changed:
                save_tasks(path, tasks)
                say(f"Marked task #{task.id} done: {task.title}", "green")
            else:
                say(f"Task #{task.id} is already done.")

        elif args.command == "month":
            console.print(render.month_view(tasks, today))

    except (TaskError, StorageError) as e:
        say(f"Error: {e}", "red")
        return 1
    return 0
