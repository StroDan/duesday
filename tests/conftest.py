import io
from datetime import date

import pytest
from rich.console import Console

TODAY = date(2026, 11, 16)  # a Monday


@pytest.fixture(autouse=True)
def fake_home(tmp_path, monkeypatch):
    """Point the home folder at a temp dir so no test can touch ~/.duesday."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    return home


@pytest.fixture
def task_file(tmp_path):
    return tmp_path / "tasks.json"


class Run:
    """Runs the CLI in-process with a fixed date and captures its output."""

    def __init__(self, task_file):
        self.task_file = task_file

    def __call__(self, *args, today=TODAY, color=False):
        from duesday.cli import main

        buf = io.StringIO()
        console = Console(
            file=buf,
            width=100,
            force_terminal=color,
            color_system="standard" if color else None,
            no_color=not color,
        )
        code = main(["--file", str(self.task_file), *args], today=today, console=console)
        return code, buf.getvalue()


@pytest.fixture
def run(task_file):
    return Run(task_file)
