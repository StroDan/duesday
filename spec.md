# duesday `plan` specification (round 1)

This spec turns the requirements in `problem.md` into exact behavior. Where the
two disagree, `problem.md` wins and this file gets fixed.

## Running

- The command is `./plan <command> [options]`, run from the repo folder.
  `./plan` with no command opens the menu (R7).
- `./plan` is a bash launcher. On first run it creates `.venv` with Python 3.12
  (prefers `/opt/homebrew/bin/python3.12`; otherwise `python3.12`, then `py -3.12`
  on Windows) and installs `requirements.txt`. It reinstalls when
  `requirements.txt` changes. Then it runs `python -m duesday`. It works in
  macOS/Linux shells and in Git Bash on Windows.
- Global option `--file PATH` uses PATH instead of the default task file. It
  can go before or after the command name.
- Exit code 0 on success, 1 on a user error (bad date, unknown task number,
  unreadable task file). Errors are printed as one line starting with
  `Error:`.

## Data model

A task has:

| field   | type                          | notes                              |
|---------|-------------------------------|------------------------------------|
| `id`    | int ≥ 1                       | unique, never reused               |
| `title` | non-empty string              | surrounding whitespace is stripped |
| `due`   | `YYYY-MM-DD` string or `null` | optional                           |
| `done`  | bool                          | `false` when the task is created   |

"Today" is always passed in as a parameter. The logic never reads the clock;
only the command-line entry point does.

### Urgency (used by R2, R4, R6)

For a given `today`, each task is in exactly one of these groups:

- **done**: `done` is true (no matter the date).
- **overdue**: not done, and `due < today`. A task due *today* is not overdue.
- **soon**: not done, and `today ≤ due ≤ today + 3 days` (inclusive).
- **later**: not done, and `due > today + 3 days`.
- **no date**: not done, and `due` is null.

## R1 Add a task

`plan add "TITLE" [--due YYYY-MM-DD]`

- Creates a task with the next number: one more than the highest existing id,
  starting at 1.
- Prints `Added task #N: TITLE` (plus the due date if one was given).
- `--due` must be a real calendar date in `YYYY-MM-DD` form, otherwise exit 1
  and save nothing. Past dates are allowed; the task is simply overdue.
- An empty or whitespace-only title is rejected with exit 1.

## R2 List tasks by urgency

`plan list`

Shows every task in this order:

1. overdue, oldest due date first
2. upcoming (soon + later), soonest due date first
3. no date
4. done

Ties within a group are broken by task number, lowest first. Done tasks are
ordered by task number. With no tasks, prints `No tasks yet.`

Each row shows: task number, status symbol, title, due date, and a short
relative note (`3 days overdue`, `due today`, `due tomorrow`, `in 5 days`).

## R3 Mark a task done

`plan done N`

- Sets `done` to true for task N, saves, and prints `Marked task #N done: TITLE`.
- The task stays in the file and in `plan list`, shown as done.
- Unknown number: exit 1 with `Error: no task #N`, file unchanged.
- Already done: prints `Task #N is already done.`, exit 0.

## R4 Month view

`plan month`

- Prints a calendar grid of the month that contains `today`, weeks starting
  on Sunday, with the title `Month YYYY` (e.g. `November 2026`).
- Each day is marked:
  - **overdue** (red, `⚠`) if any unfinished task due that day is overdue;
  - otherwise **due** (`•` and a count of tasks) if any task, done or not, is
    due that day;
  - otherwise unmarked.
- A done task never makes a day overdue.
- Today's date is highlighted.
- Below the grid: a legend, and if overdue tasks exist in earlier months, a
  line `N overdue task(s) from earlier months`, so they are not hidden.

## R5 Save tasks between runs

- Default file: `~/.duesday/tasks.json`, the same list from any folder. The
  folder is created when the first task is saved.
- `--file PATH` overrides it (used by tests; tests never touch `~/.duesday`).
- Format: `{"tasks": [ {id, title, due, done}, ... ]}`, UTF-8, indented.
- A missing file means no tasks. A file that is not valid JSON in this format
  gives exit 1 with an error, and is not overwritten.
- Writes go to a temporary file in the same folder and are then renamed over
  the old one, so a crash cannot leave a half-written file.

## R6 Make urgency stand out

In `plan list`:

| group   | style            | symbol |
|---------|------------------|--------|
| overdue | red, bold        | `⚠`    |
| soon    | yellow, bold     | `!`    |
| later   | normal           | `·`    |
| no date | normal           | `·`    |
| done    | dim              | `✔`    |

Colors come from `rich`; they are turned off automatically when output is not
a terminal (or `NO_COLOR` is set). The symbols are always shown, so urgency is
still visible without color.

## R7 Menu

`plan` (no command; `--file PATH` is still allowed)

- If standard input is a terminal, the menu opens. Otherwise (a script, a
  pipe) it prints the one-line usage (`usage: plan [-h] [--file FILE] command ...`)
  and exits 0 without reading input, so it never hangs.
- The menu screen shows the title and these options:

  ```
  1  Add a task
  2  List tasks
  3  Mark a task done
  4  Month view
  q  Quit
  ```

  then asks `Choose: `. Surrounding spaces are ignored and `Q` works like `q`.
  Anything else prints `Choose 1-4 or q.` and asks again on the same screen.
- **1 Add** asks `Title: ` (asks again if empty) and then
  `Due date (YYYY-MM-DD, blank for none): ` (blank means no date; an invalid
  date shows the error in red and asks again). Then it saves the task and prints the
  same `Added task #N: ...` line as `plan add`.
- **2 List** prints the same output as `plan list`.
- **3 Done** first shows the task list (or `No tasks yet.` and skips to "Press Enter"), then
  asks `Task number: `. Input that is not a whole number asks again. Task
  errors (`no task #N`) are shown in red. Otherwise prints the same lines as
  `plan done N`.
- **4 Month** prints the same output as `plan month`.
- After each action the menu shows a tip with the equivalent command, e.g.
  `Tip: ./plan add "Essay" --due 2026-11-20`, then
  `Press Enter to return to the menu`. The tip includes `--file PATH` when the
  menu uses a non-default file. (For a done that failed, no tip is shown.)
- Tasks are loaded from the file at the start of every action, so the menu
  always shows what is on disk. A storage error is shown in red and the menu
  carries on.
- `q` prints `Bye!` and exits 0. Ctrl+C or end of input at any prompt also
  prints `Bye!` and exits 0, with no traceback.
- The menu uses the same functions as the commands (`add_task`, `parse_due`,
  `mark_done`, `sort_tasks`, `load_tasks`, `save_tasks`, `render.task_table`,
  `render.month_view`), so behavior cannot drift between the two.

## R8 Clear screen in the menu

- The screen is cleared (`console.clear()`) right before each menu screen is
  drawn: when the menu opens and each time the user returns to it.
- Re-asking after an invalid choice does not clear again (same screen).
- Action results are not cleared until the user presses Enter.
- Only `duesday/menu.py` clears. `plan add/list/done/month` and the
  no-terminal usage message never clear, so earlier output stays visible.
- When output is not a terminal, `rich` turns `clear()` into a no-op.

## Code layout

- `duesday/tasks.py`: Task model, urgency, sorting, add/done (pure logic, no printing).
- `duesday/storage.py`: load/save JSON, default path.
- `duesday/render.py`: builds `rich` tables/text from tasks + today.
- `duesday/cli.py`: argument parsing; the only place that reads the clock. Prints
  command output, and opens the menu when there is no command.
- `duesday/menu.py`: the interactive menu (R7, R8). Gets `path`, `today`, a
  `console` and an `ask` input function as parameters, so it never reads the clock or
  stdin directly and tests can supply answers. It prints only through the console it is given.
- `tests/`: pytest; every test name starts with the requirement ID it checks.
