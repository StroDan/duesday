import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from conftest import TODAY
from duesday.cli import main
from duesday.storage import StorageError, default_path, load_tasks, save_tasks
from duesday.tasks import Task

REPO = Path(__file__).resolve().parent.parent


def test_R5_save_and_load_round_trip(task_file):
    tasks = [Task(1, "Essay", date(2026, 11, 22)), Task(2, "Ünïcode ✔", None, done=True)]
    save_tasks(task_file, tasks)
    assert load_tasks(task_file) == tasks


def test_R5_file_format_is_readable_json(task_file):
    save_tasks(task_file, [Task(1, "Essay", date(2026, 11, 22))])
    data = json.loads(task_file.read_text(encoding="utf-8"))
    assert data == {"tasks": [{"id": 1, "title": "Essay", "due": "2026-11-22", "done": False}]}


def test_R5_missing_file_means_no_tasks(tmp_path):
    assert load_tasks(tmp_path / "nope.json") == []


def test_R5_save_creates_parent_folder(tmp_path):
    path = tmp_path / "a" / "b" / "tasks.json"
    save_tasks(path, [Task(1, "x", None)])
    assert load_tasks(path) == [Task(1, "x", None)]


def test_R5_save_leaves_no_temp_files(tmp_path):
    folder = tmp_path / "store"  # tmp_path itself also holds the fake home folder
    path = folder / "tasks.json"
    save_tasks(path, [Task(1, "x", None)])
    save_tasks(path, [Task(1, "y", None)])
    assert [p.name for p in folder.iterdir()] == ["tasks.json"]


@pytest.mark.parametrize("content", ["not json", "[]", '{"tasks": [{"id": "x"}]}'])
def test_R5_corrupt_file_raises(task_file, content):
    task_file.write_text(content)
    with pytest.raises(StorageError):
        load_tasks(task_file)


def test_R5_cli_corrupt_file_is_reported_and_not_overwritten(run, task_file):
    task_file.write_text("garbage")
    code, out = run("add", "x")
    assert code == 1
    assert "Error:" in out
    assert task_file.read_text() == "garbage"


def test_R5_default_path_is_in_home_duesday(fake_home):
    assert default_path() == fake_home / ".duesday" / "tasks.json"


def test_R5_cli_without_file_uses_home_file(fake_home, tmp_path, monkeypatch):
    import io
    from rich.console import Console

    monkeypatch.chdir(tmp_path)
    console = Console(file=io.StringIO(), no_color=True)
    assert main(["add", "Shared task"], today=TODAY, console=console) == 0
    assert load_tasks(fake_home / ".duesday" / "tasks.json")[0].title == "Shared task"


def test_R5_file_option_after_command(task_file):
    import io
    from rich.console import Console

    console = Console(file=io.StringIO(), no_color=True)
    assert main(["add", "x", "--file", str(task_file)], today=TODAY, console=console) == 0
    assert load_tasks(task_file)[0].title == "x"


def test_R5_tasks_survive_separate_program_runs(task_file):
    def plan(*args):
        return subprocess.run(
            [sys.executable, "-m", "duesday", "--file", str(task_file), *args],
            cwd=REPO, capture_output=True, text=True, encoding="utf-8",
        )

    assert plan("add", "Persisted task", "--due", "2030-01-01").returncode == 0
    result = plan("list")
    assert result.returncode == 0
    assert "Persisted task" in result.stdout
