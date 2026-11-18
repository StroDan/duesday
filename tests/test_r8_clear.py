import io
import sys

import pytest

from duesday.cli import main
from duesday.storage import save_tasks
from duesday.tasks import Task

from conftest import TODAY, ClearCountingConsole, make_console

MARK = ClearCountingConsole.CLEAR_MARK


def test_R8_screen_cleared_before_first_menu_screen(menu):
    _, out = menu("q")
    assert out.startswith(MARK)
    assert out.index(MARK) < out.index("q  Quit")
    assert menu.console.clears == 1


def test_R8_cleared_once_per_menu_screen(menu, task_file):
    save_tasks(task_file, [Task(1, "a")])
    menu("2", "", "4", "", "3", "1", "", "1", "Essay", "", "", "q")
    assert menu.console.clears == 5  # first screen + one return after each of 4 actions


def test_R8_every_menu_screen_starts_right_after_a_clear(menu):
    _, out = menu("2", "", "4", "", "q")
    screens = out.split(MARK)[1:]
    assert len(screens) == 3
    for screen in screens:
        assert screen.lstrip().split("\n")[0].strip() != ""  # something is drawn
        assert "q  Quit" in screen


def test_R8_bad_choice_does_not_clear_again(menu):
    _, out = menu("x", "9", "q")
    assert menu.console.clears == 1
    assert out.count("Choose 1-4 or q.") == 2


def test_R8_results_stay_until_enter_is_pressed(menu, task_file):
    save_tasks(task_file, [Task(1, "Visible task")])
    _, out = menu("2", "", "q")
    # No clear between choosing "2" and the "Press Enter" prompt.
    [clears_at_enter] = [c for p, c in menu.prompts if "Press Enter" in p]
    assert clears_at_enter == 1
    result = out.split(MARK)[1]
    assert "Visible task" in result


def test_R8_questions_inside_an_action_do_not_clear(menu):
    menu("1", "", "Essay", "bad", "2026-11-20", "", "q")
    inside = [c for p, c in menu.prompts if "Title" in p or "Due date" in p]
    assert inside == [1, 1, 1, 1]


@pytest.mark.parametrize(
    "args",
    [
        ("add", "Essay", "--due", "2026-11-20"),
        ("add", "Bad", "--due", "nope"),
        ("list",),
        ("done", "1"),
        ("done", "99"),
        ("month",),
    ],
)
def test_R8_normal_commands_never_clear(task_file, args):
    save_tasks(task_file, [Task(1, "a")])
    console, buf = make_console()
    main(["--file", str(task_file), *args], today=TODAY, console=console)
    assert console.clears == 0
    assert MARK not in buf.getvalue()


def test_R8_usage_without_terminal_does_not_clear(task_file, monkeypatch):
    class NotATty(io.StringIO):
        def isatty(self):
            return False

    monkeypatch.setattr(sys, "stdin", NotATty(""))
    console, _ = make_console()
    assert main(["--file", str(task_file)], today=TODAY, console=console) == 0
    assert console.clears == 0
