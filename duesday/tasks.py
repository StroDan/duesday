"""Task model and rules: urgency, sorting, adding, completing.

Pure logic: nothing here prints or reads the clock. "today" is always passed in.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

SOON_DAYS = 3


class TaskError(Exception):
    """A user-facing problem with a task command (bad input, unknown number)."""


@dataclass
class Task:
    id: int
    title: str
    due: date | None = None
    done: bool = False


class Urgency(Enum):
    OVERDUE = "overdue"
    SOON = "soon"
    LATER = "later"
    NO_DATE = "no date"
    DONE = "done"


def urgency(task: Task, today: date) -> Urgency:
    if task.done:
        return Urgency.DONE
    if task.due is None:
        return Urgency.NO_DATE
    if task.due < today:
        return Urgency.OVERDUE
    if task.due <= today + timedelta(days=SOON_DAYS):
        return Urgency.SOON
    return Urgency.LATER


def sort_tasks(tasks: list[Task], today: date) -> list[Task]:
    """Overdue (oldest first), upcoming (soonest first), no date, done; ties by id."""
    group_rank = {
        Urgency.OVERDUE: 0,
        Urgency.SOON: 1,
        Urgency.LATER: 1,
        Urgency.NO_DATE: 2,
        Urgency.DONE: 3,
    }

    def key(task: Task):
        rank = group_rank[urgency(task, today)]
        by_date = task.due if rank in (0, 1) else date.min
        return (rank, by_date, task.id)

    return sorted(tasks, key=key)


def parse_due(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        raise TaskError(f"'{text}' is not a valid date; use YYYY-MM-DD, e.g. 2026-11-22") from None


def add_task(tasks: list[Task], title: str, due: date | None = None) -> Task:
    title = title.strip()
    if not title:
        raise TaskError("the task title cannot be empty")
    next_id = max((t.id for t in tasks), default=0) + 1
    task = Task(next_id, title, due)
    tasks.append(task)
    return task


def find_task(tasks: list[Task], task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise TaskError(f"no task #{task_id}")


def mark_done(tasks: list[Task], task_id: int) -> tuple[Task, bool]:
    """Mark a task done. Returns the task and whether it changed."""
    task = find_task(tasks, task_id)
    if task.done:
        return task, False
    task.done = True
    return task, True


@dataclass
class DayMark:
    count: int = 0
    overdue: bool = False


def month_marks(tasks: list[Task], year: int, month: int, today: date) -> dict[int, DayMark]:
    """Map day-of-month -> mark for every day in the month that has a task due."""
    marks: dict[int, DayMark] = {}
    for task in tasks:
        if task.due is None or (task.due.year, task.due.month) != (year, month):
            continue
        mark = marks.setdefault(task.due.day, DayMark())
        mark.count += 1
        if urgency(task, today) is Urgency.OVERDUE:
            mark.overdue = True
    return marks


def overdue_before_month(tasks: list[Task], year: int, month: int, today: date) -> int:
    first = date(year, month, 1)
    return sum(
        1 for t in tasks
        if urgency(t, today) is Urgency.OVERDUE and t.due is not None and t.due < first
    )
