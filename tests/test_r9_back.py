import pytest

from duesday.storage import load_tasks, save_tasks
from duesday.tasks import Task

from conftest import ClearCountingConsole

MARK = ClearCountingConsole.CLEAR_MARK
BACK = "Back to the menu, nothing was saved."
HINT = "(b to go back)"


@pytest.fixture
def one_task(task_file):
    save_tasks(task_file, [Task(1, "Essay")])
    return task_file.read_bytes()


def assert_went_back(menu, out):
    """b ended the action: message shown, no tip, no Press Enter, next screen is the menu."""
    assert BACK in out
    assert "Tip:" not in out
    assert not menu.asked("Press Enter")
    assert menu.asked("Choose") == 2
    after = out.split(BACK, 1)[1]
    assert after.lstrip().startswith(MARK.strip())  # straight to a cleared menu screen
    assert "q  Quit" in after
    assert "Bye!" in out


# --- going back -------------------------------------------------------------


@pytest.mark.parametrize("answer", ["b", "B", "  b  "])
def test_R9_b_at_title_returns_to_menu_and_saves_nothing(menu, task_file, one_task, answer):
    code, out = menu("1", answer, "q")
    assert code == 0
    assert_went_back(menu, out)
    assert not menu.asked("Due date")
    assert task_file.read_bytes() == one_task


def test_R9_b_at_title_with_no_file_creates_no_file(menu, task_file):
    code, out = menu("1", "b", "q")
    assert code == 0
    assert_went_back(menu, out)
    assert not task_file.exists()


@pytest.mark.parametrize("answer", ["b", "B", " B "])
def test_R9_b_at_due_date_returns_to_menu_and_saves_nothing(menu, task_file, one_task, answer):
    code, out = menu("1", "Lab report", answer, "q")
    assert code == 0
    assert_went_back(menu, out)
    assert task_file.read_bytes() == one_task
    assert [t.title for t in load_tasks(task_file)] == ["Essay"]


def test_R9_b_at_due_date_after_bad_date_still_goes_back(menu, task_file, one_task):
    code, out = menu("1", "Lab report", "2026-13-01", "b", "q")
    assert code == 0
    assert BACK in out
    assert task_file.read_bytes() == one_task


@pytest.mark.parametrize("answer", ["b", "B", " b"])
def test_R9_b_at_task_number_returns_to_menu_and_changes_nothing(menu, task_file, one_task, answer):
    code, out = menu("3", answer, "q")
    assert code == 0
    assert_went_back(menu, out)
    assert "Type the task's number" not in out  # b is not treated as a bad number
    assert task_file.read_bytes() == one_task
    assert not load_tasks(task_file)[0].done


def test_R9_menu_works_normally_after_going_back(menu, task_file):
    code, out = menu("1", "b", "1", "Essay", "", "", "q")
    assert code == 0
    assert [t.title for t in load_tasks(task_file)] == ["Essay"]
    assert "Added task #1: Essay" in out


# --- the hint ----------------------------------------------------------------


def test_R9_title_question_shows_hint(menu):
    menu("1", "b", "q")
    assert any(p.startswith("Title") and HINT in p for p, _ in menu.prompts)


def test_R9_due_date_question_shows_hint(menu):
    menu("1", "Essay", "b", "q")
    assert any(p.startswith("Due date") and HINT in p for p, _ in menu.prompts)


def test_R9_task_number_question_shows_hint(menu, one_task):
    menu("3", "b", "q")
    assert any(p.startswith("Task number") and HINT in p for p, _ in menu.prompts)


def test_R9_every_action_question_shows_hint(menu, one_task):
    menu("1", "", "Essay", "bad", "", "", "3", "x", "b", "q")
    questions = [p for p, _ in menu.prompts if not p.startswith(("Choose", "Press Enter"))]
    assert len(questions) == 6  # 2 titles, 2 due dates, 2 task numbers (re-asks included)
    assert all(HINT in p for p in questions)


def test_R9_choose_prompt_has_no_hint(menu):
    _, out = menu("b", "q")
    assert all(HINT not in p for p, _ in menu.prompts if p.startswith("Choose"))
    assert "Choose 1-4 or q." in out
