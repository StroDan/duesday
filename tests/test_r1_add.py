from datetime import date

import pytest

from duesday.storage import load_tasks
from duesday.tasks import TaskError, add_task, parse_due


def test_R1_add_task_with_title_and_due_date():
    tasks = []
    task = add_task(tasks, "CSC299 final", date(2026, 11, 22))
    assert task.id == 1
    assert task.title == "CSC299 final"
    assert task.due == date(2026, 11, 22)
    assert task.done is False
    assert tasks == [task]


def test_R1_due_date_is_optional():
    task = add_task([], "Buy groceries")
    assert task.due is None


def test_R1_each_task_gets_the_next_number():
    tasks = []
    ids = [add_task(tasks, f"t{i}").id for i in range(3)]
    assert ids == [1, 2, 3]


def test_R1_numbers_continue_after_highest_existing_id():
    tasks = []
    add_task(tasks, "a")
    add_task(tasks, "b")
    tasks.pop(0)  # leave only #2
    assert add_task(tasks, "c").id == 3


def test_R1_title_whitespace_is_stripped():
    assert add_task([], "  Essay  ").title == "Essay"


def test_R1_empty_title_is_rejected():
    with pytest.raises(TaskError):
        add_task([], "   ")


@pytest.mark.parametrize("text", ["2026-13-01", "2026-02-30", "11/22/2026", "tomorrow", ""])
def test_R1_invalid_due_date_is_rejected(text):
    with pytest.raises(TaskError):
        parse_due(text)


def test_R1_parse_due_accepts_iso_date():
    assert parse_due("2026-11-22") == date(2026, 11, 22)


def test_R1_cli_add_prints_task_number(run, task_file):
    code, out = run("add", "CSC299 final", "--due", "2026-11-22")
    assert code == 0
    assert "Added task #1: CSC299 final" in out
    assert "2026-11-22" in out
    code, out = run("add", "Laundry")
    assert "Added task #2: Laundry" in out
    tasks = load_tasks(task_file)
    assert [(t.id, t.title, t.due) for t in tasks] == [
        (1, "CSC299 final", date(2026, 11, 22)),
        (2, "Laundry", None),
    ]


def test_R1_cli_add_with_bad_date_saves_nothing(run, task_file):
    code, out = run("add", "Essay", "--due", "2026-02-30")
    assert code == 1
    assert out.startswith("Error:")
    assert not task_file.exists()


def test_R1_cli_add_with_empty_title_fails(run, task_file):
    code, out = run("add", "  ")
    assert code == 1
    assert "Error:" in out
    assert not task_file.exists()
