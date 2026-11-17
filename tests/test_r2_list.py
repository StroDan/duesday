from datetime import date, timedelta

from conftest import TODAY
from duesday.tasks import Task, Urgency, sort_tasks, urgency


def d(offset):
    return TODAY + timedelta(days=offset)


def test_R2_order_overdue_upcoming_nodate_done():
    tasks = [
        Task(1, "no date", None),
        Task(2, "done", d(-5), done=True),
        Task(3, "later", d(10)),
        Task(4, "overdue", d(-2)),
        Task(5, "soon", d(1)),
    ]
    assert [t.title for t in sort_tasks(tasks, TODAY)] == [
        "overdue", "soon", "later", "no date", "done",
    ]


def test_R2_overdue_oldest_first():
    tasks = [Task(1, "a", d(-1)), Task(2, "b", d(-10)), Task(3, "c", d(-3))]
    assert [t.id for t in sort_tasks(tasks, TODAY)] == [2, 3, 1]


def test_R2_upcoming_soonest_first():
    tasks = [Task(1, "a", d(20)), Task(2, "b", d(0)), Task(3, "c", d(4)), Task(4, "e", d(2))]
    assert [t.id for t in sort_tasks(tasks, TODAY)] == [2, 4, 3, 1]


def test_R2_ties_broken_by_task_number():
    tasks = [Task(3, "a", d(2)), Task(1, "b", d(2)), Task(5, "x", None), Task(2, "y", None)]
    assert [t.id for t in sort_tasks(tasks, TODAY)] == [1, 3, 2, 5]


def test_R2_done_tasks_last_by_number():
    tasks = [Task(4, "a", d(-9), done=True), Task(2, "b", None, done=True), Task(3, "c", None)]
    assert [t.id for t in sort_tasks(tasks, TODAY)] == [3, 2, 4]


def test_R2_due_today_is_upcoming_not_overdue():
    assert urgency(Task(1, "t", TODAY), TODAY) is Urgency.SOON
    assert urgency(Task(1, "t", d(-1)), TODAY) is Urgency.OVERDUE


def test_R2_sort_does_not_modify_input():
    tasks = [Task(1, "a", d(5)), Task(2, "b", d(-1))]
    sort_tasks(tasks, TODAY)
    assert [t.id for t in tasks] == [1, 2]


def test_R2_cli_list_shows_tasks_in_urgency_order(run):
    run("add", "No date task")
    run("add", "Later task", "--due", "2026-12-20")
    run("add", "Overdue task", "--due", "2026-11-10")
    run("add", "Soon task", "--due", "2026-11-17")
    run("done", "2")
    code, out = run("list")
    assert code == 0
    positions = [out.index(name) for name in ["Overdue task", "Soon task", "No date task", "Later task"]]
    assert positions == sorted(positions)


def test_R2_cli_list_shows_relative_notes(run):
    run("add", "A", "--due", "2026-11-13")
    run("add", "B", "--due", "2026-11-16")
    run("add", "C", "--due", "2026-11-17")
    run("add", "D", "--due", "2026-11-21")
    _, out = run("list")
    assert "3 days overdue" in out
    assert "due today" in out
    assert "due tomorrow" in out
    assert "in 5 days" in out


def test_R2_cli_list_empty(run):
    code, out = run("list")
    assert code == 0
    assert "No tasks yet." in out


def test_R2_list_uses_given_today():
    task = Task(1, "t", date(2026, 11, 20))
    assert urgency(task, date(2026, 11, 21)) is Urgency.OVERDUE
    assert urgency(task, date(2026, 11, 1)) is Urgency.LATER
