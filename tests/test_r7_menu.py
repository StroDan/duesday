import builtins
import io
import sys

import pytest

from duesday.cli import main
from duesday.storage import default_path, load_tasks, save_tasks
from duesday.tasks import Task

from conftest import TODAY, make_console

MENU_LINES = ["1  Add a task", "2  List tasks", "3  Mark a task done", "4  Month view", "q  Quit"]


class FakeStdin(io.StringIO):
    def __init__(self, tty):
        super().__init__("")
        self._tty = tty

    def isatty(self):
        return self._tty


def no_input(*_args, **_kwargs):
    raise AssertionError("input() must not be called")


# --- opening the menu -------------------------------------------------------


def test_R7_no_command_without_terminal_prints_usage_and_exits_0(task_file, monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStdin(tty=False))
    monkeypatch.setattr(builtins, "input", no_input)
    console, buf = make_console()
    code = main(["--file", str(task_file)], today=TODAY, console=console)
    out = buf.getvalue()
    assert code == 0
    assert out.startswith("usage: plan")
    assert "[--file FILE]" in out  # brackets are not eaten as rich markup
    assert "Quit" not in out
    assert not task_file.exists()


def test_R7_no_command_in_terminal_opens_menu(task_file, monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStdin(tty=True))
    answers = iter(["1", "Essay", "2026-11-20", "", "q"])
    monkeypatch.setattr(builtins, "input", lambda *a: next(answers))
    console, buf = make_console()
    code = main(["--file", str(task_file)], today=TODAY, console=console)
    out = buf.getvalue()
    assert code == 0
    for line in MENU_LINES:
        assert line in out
    assert "Bye!" in out
    assert [(t.title, str(t.due)) for t in load_tasks(task_file)] == [("Essay", "2026-11-20")]


def test_R7_menu_lists_all_options(menu):
    code, out = menu("q")
    assert code == 0
    for line in MENU_LINES:
        assert line in out
    assert menu.asked("Choose")


# --- choices ----------------------------------------------------------------


def test_R7_bad_choice_says_choose_1_4_or_q(menu):
    code, out = menu("7", "add", "", "q")
    assert code == 0
    assert out.count("Choose 1-4 or q.") == 3
    assert menu.asked("Choose") == 4


def test_R7_q_is_case_insensitive_and_trimmed(menu):
    code, out = menu("  Q ")
    assert code == 0
    assert "Bye!" in out


def test_R7_menu_returns_after_each_action_until_quit(menu):
    code, out = menu("2", "", "4", "", "q")
    assert code == 0
    assert out.count("q  Quit") == 3
    assert menu.asked("Press Enter to return to the menu") == 2


# --- add --------------------------------------------------------------------


def test_R7_add_with_due_date(menu, task_file):
    code, out = menu("1", "Essay", "2026-11-20", "", "q")
    assert code == 0
    assert "Added task #1: Essay (due 2026-11-20)" in out
    assert f'Tip: ./plan add "Essay" --due 2026-11-20 --file {task_file}' in out
    assert menu.asked("Press Enter to return to the menu") == 1
    [task] = load_tasks(task_file)
    assert (task.title, str(task.due), task.done) == ("Essay", "2026-11-20", False)


def test_R7_add_due_date_can_be_skipped(menu, task_file):
    code, out = menu("1", "Laundry", "", "", "q")
    assert code == 0
    assert "Added task #1: Laundry" in out
    assert "(due" not in out
    assert "Tip: ./plan add \"Laundry\" --file" in out
    assert "--due" not in out
    assert load_tasks(task_file)[0].due is None


def test_R7_add_reasks_empty_title(menu, task_file):
    code, out = menu("1", "", "   ", "Essay", "", "", "q")
    assert code == 0
    assert menu.asked("Title") == 3
    assert [t.title for t in load_tasks(task_file)] == ["Essay"]


def test_R7_add_reasks_bad_date(menu, task_file):
    code, out = menu("1", "Essay", "2026-13-01", "next week", "2026-11-20", "", "q")
    assert code == 0
    assert menu.asked("Due date") == 3
    assert "not a valid date" in out
    assert str(load_tasks(task_file)[0].due) == "2026-11-20"


def test_R7_add_bad_date_error_is_red(menu):
    _, out = menu("1", "Essay", "nope", "", "", "q", color=True)
    assert "\x1b[31m" in out
    assert "not a valid date" in out


def test_R7_add_uses_next_number(menu, task_file):
    save_tasks(task_file, [Task(1, "a"), Task(5, "b")])
    _, out = menu("1", "c", "", "", "q")
    assert "Added task #6: c" in out


def test_R7_tip_quotes_titles_safely(menu):
    _, out = menu("1", 'Say "hi" for $5', "", "", "q")
    assert "Tip: ./plan add 'Say \"hi\" for $5' --file" in out


def test_R7_tip_has_no_file_option_for_default_file(menu):
    _, out = menu("2", "", "q", path=default_path())
    assert "Tip: ./plan list\n" in out


# --- list -------------------------------------------------------------------


def test_R7_list_shows_tasks_by_urgency(menu, task_file):
    save_tasks(task_file, [Task(1, "Later", TODAY.replace(day=30)), Task(2, "Late", TODAY.replace(day=2))])
    code, out = menu("2", "", "q")
    assert code == 0
    assert out.index("Late ") < out.index("Later")
    assert "⚠" in out
    assert "Tip: ./plan list --file" in out


def test_R7_list_with_no_tasks(menu):
    _, out = menu("2", "", "q")
    assert "No tasks yet." in out


# --- done -------------------------------------------------------------------


def test_R7_done_marks_task_and_shows_tip(menu, task_file):
    save_tasks(task_file, [Task(1, "a"), Task(2, "Lab 4")])
    code, out = menu("3", "2", "", "q")
    assert code == 0
    assert "Marked task #2 done: Lab 4" in out
    assert "Tip: ./plan done 2 --file" in out
    assert [t.done for t in load_tasks(task_file)] == [False, True]


def test_R7_done_shows_tasks_before_asking(menu, task_file):
    save_tasks(task_file, [Task(1, "Read chapter 4")])
    _, out = menu("3", "1", "", "q")
    assert out.index("Read chapter 4") < out.index("Task number")


def test_R7_done_reasks_non_numbers(menu, task_file):
    save_tasks(task_file, [Task(1, "a")])
    _, out = menu("3", "", "one", "1.5", "1", "", "q")
    assert menu.asked("Task number") == 4
    assert load_tasks(task_file)[0].done is True


def test_R7_done_unknown_number_shown_in_red(menu, task_file):
    save_tasks(task_file, [Task(1, "a")])
    before = task_file.read_text()
    code, out = menu("3", "9", "", "q", color=True)
    assert code == 0
    assert "Error: no task #9" in out
    assert "\x1b[31m" in out
    assert "Tip:" not in out
    assert task_file.read_text() == before


def test_R7_done_already_done(menu, task_file):
    save_tasks(task_file, [Task(1, "a", done=True)])
    _, out = menu("3", "1", "", "q")
    assert "Task #1 is already done." in out


def test_R7_done_with_no_tasks_does_not_ask(menu):
    _, out = menu("3", "", "q")
    assert "No tasks yet." in out
    assert menu.asked("Task number") == 0


# --- month ------------------------------------------------------------------


def test_R7_month_shows_calendar(menu, task_file):
    save_tasks(task_file, [Task(1, "a", TODAY.replace(day=2))])
    _, out = menu("4", "", "q")
    assert "November 2026" in out
    assert "⚠" in out
    assert "Tip: ./plan month --file" in out


# --- leaving ----------------------------------------------------------------


@pytest.mark.parametrize(
    "answers",
    [
        ("1",),                     # end of input at the title prompt
        ("1", "Essay"),             # ... at the due date prompt
        ("3",),                     # ... at "Press Enter" after "No tasks yet."
        ("2",),                     # ... at "Press Enter"
        (),                         # ... at the first menu prompt
    ],
)
def test_R7_end_of_input_exits_with_bye(menu, answers):
    code, out = menu(*answers)
    assert code == 0
    assert out.rstrip().endswith("Bye!")
    assert "Traceback" not in out


@pytest.mark.parametrize("answers", [(KeyboardInterrupt,), ("1", KeyboardInterrupt), ("2", KeyboardInterrupt)])
def test_R7_ctrl_c_exits_with_bye(menu, answers, task_file):
    code, out = menu(*answers)
    assert code == 0
    assert out.rstrip().endswith("Bye!")
    assert not task_file.exists()


def test_R7_storage_error_shown_and_menu_continues(menu, task_file):
    task_file.write_text("not json")
    code, out = menu("2", "", "q")
    assert code == 0
    assert "Error:" in out
    assert "Bye!" in out
    assert task_file.read_text() == "not json"


# --- same data as the commands ----------------------------------------------


def test_R7_menu_and_commands_share_the_task_file(menu, run):
    run("add", "From command")
    menu("1", "From menu", "", "", "q")
    _, out = run("list")
    assert "From command" in out
    assert "From menu" in out
