from datetime import timedelta

import pytest

from conftest import TODAY
from duesday.render import style_for, symbol_for
from duesday.tasks import Task, Urgency, urgency


def d(offset):
    return TODAY + timedelta(days=offset)


@pytest.mark.parametrize(
    "offset,expected",
    [(-1, Urgency.OVERDUE), (0, Urgency.SOON), (3, Urgency.SOON), (4, Urgency.LATER)],
)
def test_R6_three_day_window_is_inclusive(offset, expected):
    assert urgency(Task(1, "t", d(offset)), TODAY) is expected


def test_R6_done_overrides_date():
    assert urgency(Task(1, "t", d(-5), done=True), TODAY) is Urgency.DONE
    assert urgency(Task(1, "t", None), TODAY) is Urgency.NO_DATE


def test_R6_symbols_and_styles():
    assert symbol_for(Urgency.OVERDUE) == "⚠"
    assert "red" in style_for(Urgency.OVERDUE)
    assert symbol_for(Urgency.DONE) == "✔"
    assert "dim" in style_for(Urgency.DONE)
    assert "yellow" in style_for(Urgency.SOON)
    assert "red" not in style_for(Urgency.LATER)


def _line_with(out, text):
    return next(line for line in out.splitlines() if text in line)


def test_R6_cli_list_colors_rows(run):
    run("add", "Overdue essay", "--due", "2026-11-12")
    run("add", "Soon quiz", "--due", "2026-11-19")
    run("add", "Far project", "--due", "2026-12-15")
    run("add", "Finished lab", "--due", "2026-11-18")
    run("done", "4")
    _, out = run("list", color=True)
    overdue = _line_with(out, "Overdue essay")
    assert "⚠" in overdue and "\x1b[1;31m" in overdue  # bold red
    assert "\x1b[1;33m" in _line_with(out, "Soon quiz")  # bold yellow
    far = _line_with(out, "Far project")
    assert "31m" not in far and "33m" not in far
    done = _line_with(out, "Finished lab")
    assert "✔" in done and "\x1b[2m" in done  # dim


def test_R6_symbols_visible_without_color(run):
    run("add", "Overdue essay", "--due", "2026-11-12")
    run("add", "Done lab")
    run("done", "2")
    _, out = run("list", color=False)
    assert "\x1b[" not in out
    assert "⚠" in _line_with(out, "Overdue essay")
    assert "✔" in _line_with(out, "Done lab")
