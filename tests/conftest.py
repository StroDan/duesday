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


class ClearCountingConsole(Console):
    """A Console that counts clear() calls and marks each one in the output."""

    CLEAR_MARK = "<<CLEAR>>\n"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clears = 0

    def clear(self, home: bool = True) -> None:
        self.clears += 1
        self.file.write(self.CLEAR_MARK)
        super().clear(home)


def make_console(color=False, cls=ClearCountingConsole):
    buf = io.StringIO()
    console = cls(
        file=buf,
        width=100,
        force_terminal=color,
        color_system="standard" if color else None,
        no_color=not color,
    )
    return console, buf


class MenuRun:
    """Runs run_menu with scripted answers. Running out of answers acts like end of input."""

    def __init__(self, task_file):
        self.task_file = task_file
        self.prompts = []  # (prompt, clears so far) for each question asked

    def __call__(self, *answers, today=TODAY, color=False, path=None):
        from duesday.menu import run_menu

        console, buf = make_console(color)
        pending = list(answers)
        self.prompts = []

        def ask(prompt=""):
            self.prompts.append((str(prompt), console.clears))
            console.print(prompt, end="")
            if not pending:
                raise EOFError
            answer = pending.pop(0)
            if answer is KeyboardInterrupt:
                raise KeyboardInterrupt
            console.print(answer, markup=False)
            return answer

        code = run_menu(path or self.task_file, today, console, ask)
        self.console = console
        return code, buf.getvalue()

    def asked(self, text):
        return sum(1 for p, _ in self.prompts if text in p)


@pytest.fixture
def menu(task_file):
    return MenuRun(task_file)
