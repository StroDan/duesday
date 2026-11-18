"""Interactive menu (R7), with the screen cleared before each menu screen (R8)
and `b` at any action question to go back without saving (R9).

Never reads the clock or stdin itself: `today`, the console to print on and the
`ask` input function are passed in, so tests can supply the answers.
Each action reuses the same logic and rendering as the matching command.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable
from datetime import date
from pathlib import Path

from rich.console import Console
from rich.text import Text

from . import render
from .storage import StorageError, default_path, load_tasks, save_tasks
from .tasks import TaskError, add_task, mark_done, parse_due

Ask = Callable[[str], str]
# An action prints its result and returns the equivalent command's words
# (already shell-quoted) for the tip, or None when there is nothing to suggest.
Action = Callable[[Path, date, Console, Ask], "list[str] | None"]

OPTIONS = [
    ("1", "Add a task"),
    ("2", "List tasks"),
    ("3", "Mark a task done"),
    ("4", "Month view"),
    ("q", "Quit"),
]

BACK_HINT = "(b to go back)"


class BackToMenu(Exception):
    """The user typed b at an action question (R9): stop and save nothing."""


def _ask_or_back(ask: Ask, question: str) -> str:
    """Ask `question` with the R9 hint; return the trimmed answer, or raise BackToMenu on b."""
    answer = ask(f"{question} {BACK_HINT}: ").strip()
    if answer.lower() == "b":
        raise BackToMenu
    return answer


def run_menu(path: Path, today: date, console: Console, ask: Ask | None = None) -> int:
    ask = ask or console.input
    path = Path(path)
    actions: dict[str, Action] = {"1": _add, "2": _list, "3": _done, "4": _month}
    try:
        while True:
            console.clear()  # R8: every menu screen starts on a clean screen
            _draw_menu(console)
            choice = ask("Choose: ").strip().lower()
            while choice != "q" and choice not in actions:
                console.print(Text("Choose 1-4 or q.", style="yellow"))
                choice = ask("Choose: ").strip().lower()
            if choice == "q":
                break

            console.print()
            try:
                command = actions[choice](path, today, console, ask)
            except BackToMenu:
                console.print(Text("Back to the menu, nothing was saved.", style="yellow"))
                continue  # R9: straight back, no tip and no Press Enter
            except (TaskError, StorageError) as e:
                console.print(render.error_message(e))
                command = None
            if command:
                console.print()
                # soft_wrap: no hard line breaks inside a command meant to be copied
                console.print(Text(f"Tip: {_tip(command, path)}", style="cyan"), soft_wrap=True)
            console.print()
            ask("Press Enter to return to the menu")
    except (KeyboardInterrupt, EOFError):
        console.print()  # the cursor is still on the prompt line
    console.print(Text("Bye!"))
    return 0


def _draw_menu(console: Console) -> None:
    console.print(Text("plan: all your deadlines in one place", style="bold"))
    console.print()
    for key, label in OPTIONS:
        console.print(Text.assemble((key, "bold cyan"), f"  {label}"))
    console.print()


def _add(path: Path, today: date, console: Console, ask: Ask) -> list[str]:
    tasks = load_tasks(path)  # first, so a broken file is reported before any typing

    title = _ask_or_back(ask, "Title")
    while not title:
        console.print(Text("The title cannot be empty.", style="red"))
        title = _ask_or_back(ask, "Title")

    due = None
    while True:
        text = _ask_or_back(ask, "Due date (YYYY-MM-DD, blank for none)")
        if not text:
            break
        try:
            due = parse_due(text)
            break
        except TaskError as e:
            console.print(render.error_message(e))

    task = add_task(tasks, title, due)
    save_tasks(path, tasks)
    console.print(render.added_message(task))
    return ["add", _quote_title(task.title)] + (["--due", task.due.isoformat()] if task.due else [])


def _list(path: Path, today: date, console: Console, ask: Ask) -> list[str]:
    console.print(render.task_list(load_tasks(path), today))
    return ["list"]


def _done(path: Path, today: date, console: Console, ask: Ask) -> list[str] | None:
    tasks = load_tasks(path)
    console.print(render.task_list(tasks, today))  # so the numbers are on screen
    if not tasks:
        return None
    console.print()

    while True:
        text = _ask_or_back(ask, "Task number")
        try:
            number = int(text)
            break
        except ValueError:
            console.print(Text("Type the task's number, e.g. 2.", style="red"))

    task, changed = mark_done(tasks, number)
    if changed:
        save_tasks(path, tasks)
    console.print(render.done_message(task, changed))
    return ["done", str(task.id)]


def _month(path: Path, today: date, console: Console, ask: Ask) -> list[str]:
    console.print(render.month_view(load_tasks(path), today))
    return ["month"]


def _quote_title(title: str) -> str:
    """Double quotes like the README examples, unless the shell would expand something inside them."""
    if any(c in title for c in '"$`\\!'):
        return shlex.quote(title)
    return f'"{title}"'


def _tip(command: list[str], path: Path) -> str:
    words = ["./plan", *command]
    if path != default_path():
        words += ["--file", shlex.quote(str(path))]
    return " ".join(words)
