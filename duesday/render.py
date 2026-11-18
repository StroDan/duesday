"""Turn tasks into rich renderables. Builds output; does not print it."""

from __future__ import annotations

import calendar
from datetime import date

from rich.console import Group
from rich.table import Table
from rich.text import Text

from .tasks import Task, Urgency, month_marks, overdue_before_month, sort_tasks, urgency

_LOOK = {
    Urgency.OVERDUE: ("⚠", "bold red"),
    Urgency.SOON: ("!", "bold yellow"),
    Urgency.LATER: ("·", ""),
    Urgency.NO_DATE: ("·", ""),
    Urgency.DONE: ("✔", "dim"),
}


def symbol_for(u: Urgency) -> str:
    return _LOOK[u][0]


def style_for(u: Urgency) -> str:
    return _LOOK[u][1]


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def relative_note(task: Task, today: date) -> str:
    if task.done:
        return "done"
    if task.due is None:
        return ""
    days = (task.due - today).days
    if days < 0:
        return f"{_plural(-days, 'day')} overdue"
    if days == 0:
        return "due today"
    if days == 1:
        return "due tomorrow"
    return f"in {days} days"


def task_table(tasks: list[Task], today: date) -> Table:
    """Rows in the order given; caller sorts."""
    table = Table(show_edge=False, header_style="bold")
    table.add_column("#", justify="right")
    table.add_column("")
    table.add_column("Task", overflow="fold")
    table.add_column("Due", no_wrap=True)
    table.add_column("When", no_wrap=True)
    for task in tasks:
        u = urgency(task, today)
        due = task.due.strftime("%a %Y-%m-%d") if task.due else "-"
        table.add_row(
            str(task.id), symbol_for(u), Text(task.title), due, relative_note(task, today),
            style=style_for(u) or None,
        )
    return table


def task_list(tasks: list[Task], today: date) -> Table | Text:
    """What `plan list` shows: the sorted table, or a note when there are no tasks."""
    if not tasks:
        return Text("No tasks yet.")
    return task_table(sort_tasks(tasks, today), today)


def added_message(task: Task) -> Text:
    due = f" (due {task.due.isoformat()})" if task.due else ""
    return Text(f"Added task #{task.id}: {task.title}{due}", style="green")


def done_message(task: Task, changed: bool) -> Text:
    if changed:
        return Text(f"Marked task #{task.id} done: {task.title}", style="green")
    return Text(f"Task #{task.id} is already done.")


def error_message(error: Exception) -> Text:
    return Text(f"Error: {error}", style="red")


def month_weeks(year: int, month: int) -> list[list[int]]:
    """Weeks of the month starting on Sunday; 0 marks days outside the month."""
    return calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(year, month)


def month_view(tasks: list[Task], today: date) -> Group:
    year, month = today.year, today.month
    marks = month_marks(tasks, year, month, today)

    grid = Table(title=f"{calendar.month_name[month]} {year}", title_style="bold")
    for name in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
        grid.add_column(name, justify="center", min_width=6)

    for week in month_weeks(year, month):
        cells = []
        for day in week:
            if day == 0:
                cells.append("")
                continue
            cell = Text(f"{day:>2}", style="reverse" if day == today.day else "")
            mark = marks.get(day)
            if mark and mark.overdue:
                cell.append(" ⚠", style="bold red")
            elif mark:
                cell.append(f" •{mark.count}", style="bold yellow" if day >= today.day else "cyan")
            cells.append(cell)
        grid.add_row(*cells)

    legend = Text.assemble(
        ("⚠", "bold red"), " overdue   ", ("•N", "bold yellow"), " tasks due   ",
        ("today", "reverse"),
    )
    parts = [grid, legend]
    earlier = overdue_before_month(tasks, year, month, today)
    if earlier:
        parts.append(Text(f"{_plural(earlier, 'overdue task')} from earlier months", style="bold red"))
    return Group(*parts)
