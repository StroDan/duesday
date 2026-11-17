import pytest

from duesday.storage import load_tasks
from duesday.tasks import Task, TaskError, mark_done


def test_R3_mark_done_sets_flag_and_keeps_task():
    tasks = [Task(1, "a", None), Task(4, "b", None)]
    task, changed = mark_done(tasks, 4)
    assert changed is True
    assert task.done is True
    assert len(tasks) == 2
    assert tasks[0].done is False


def test_R3_mark_done_twice_reports_unchanged():
    tasks = [Task(1, "a", None, done=True)]
    task, changed = mark_done(tasks, 1)
    assert changed is False
    assert task.done is True


def test_R3_unknown_task_number_raises():
    with pytest.raises(TaskError):
        mark_done([Task(1, "a", None)], 9)


def test_R3_cli_done_saves_and_stays_listed(run, task_file):
    run("add", "Read chapter 4")
    run("add", "Lab 4")
    code, out = run("done", "2")
    assert code == 0
    assert "Marked task #2 done: Lab 4" in out
    assert [t.done for t in load_tasks(task_file)] == [False, True]
    _, out = run("list")
    assert "Lab 4" in out
    assert "✔" in out


def test_R3_cli_done_unknown_number(run, task_file):
    run("add", "Only task")
    before = task_file.read_text()
    code, out = run("done", "7")
    assert code == 1
    assert "Error: no task #7" in out
    assert task_file.read_text() == before


def test_R3_cli_done_already_done(run):
    run("add", "x")
    run("done", "1")
    code, out = run("done", "1")
    assert code == 0
    assert "Task #1 is already done." in out
