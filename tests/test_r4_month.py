import re
from datetime import date

from conftest import TODAY
from duesday.render import month_weeks
from duesday.tasks import Task, month_marks, overdue_before_month


def test_R4_grid_weeks_start_sunday():
    weeks = month_weeks(2026, 11)
    # November 1, 2026 is a Sunday; November 30 is a Monday.
    assert weeks[0][:7] == [1, 2, 3, 4, 5, 6, 7]
    assert weeks[-1] == [29, 30, 0, 0, 0, 0, 0]
    assert len(weeks) == 5


def test_R4_grid_pads_first_week():
    weeks = month_weeks(2026, 12)  # Dec 1, 2026 is a Tuesday
    assert weeks[0] == [0, 0, 1, 2, 3, 4, 5]


def test_R4_marks_days_with_tasks_and_overdue():
    tasks = [
        Task(1, "past due", date(2026, 11, 10)),
        Task(2, "upcoming", date(2026, 11, 22)),
        Task(3, "upcoming 2", date(2026, 11, 22)),
        Task(4, "other month", date(2026, 12, 1)),
        Task(5, "no date", None),
    ]
    marks = month_marks(tasks, 2026, 11, TODAY)
    assert set(marks) == {10, 22}
    assert marks[10].overdue is True and marks[10].count == 1
    assert marks[22].overdue is False and marks[22].count == 2


def test_R4_done_task_marks_day_but_never_overdue():
    tasks = [Task(1, "done past", date(2026, 11, 3), done=True)]
    marks = month_marks(tasks, 2026, 11, TODAY)
    assert marks[3].count == 1
    assert marks[3].overdue is False


def test_R4_day_overdue_if_any_unfinished_task_overdue():
    tasks = [
        Task(1, "done", date(2026, 11, 5), done=True),
        Task(2, "not done", date(2026, 11, 5)),
    ]
    marks = month_marks(tasks, 2026, 11, TODAY)
    assert marks[5].overdue is True
    assert marks[5].count == 2


def test_R4_counts_overdue_from_earlier_months():
    tasks = [
        Task(1, "old", date(2026, 10, 30)),
        Task(2, "old done", date(2026, 10, 1), done=True),
        Task(3, "this month", date(2026, 11, 2)),
    ]
    assert overdue_before_month(tasks, 2026, 11, TODAY) == 1


def test_R4_cli_month_shows_current_month_grid(run):
    run("add", "Past", "--due", "2026-11-10")
    run("add", "Final", "--due", "2026-11-22")
    run("add", "Older", "--due", "2026-10-02")
    code, out = run("month")
    assert code == 0
    assert "November 2026" in out
    for name in ["Sun", "Mon", "Sat"]:
        assert name in out
    assert re.search(r"\b30\b", out)
    assert "⚠" in out
    assert "•" in out
    assert "1 overdue task from earlier months" in out


def test_R4_cli_month_follows_today(run):
    code, out = run("month", today=date(2027, 2, 3))
    assert code == 0
    assert "February 2027" in out
    assert not re.search(r"\b29\b", out)
