# Problem
A college student taking several courses at once. Each course posts its
deadlines in a different place: D2L, emails from the instructor, a
syllabus PDF, or a note scribbled during lecture. On top of that there
are non-school tasks like work shifts, errands, and appointments.

Deadlines are scattered. There is no single place that shows everything
that is due, so the student has to check several sites and notes to
piece together the week. It's hard to see what's urgent. Even when the
tasks are written down, they aren't sorted by due date, so something due
tomorrow can sit unnoticed below something due next month. Overdue items
slip by quietly. Nothing flags a task once its date has passed, so a
missed deadline is often discovered only after it's too late to ask for
an extension. There's no overview of the month. The student can't easily
see which weeks are packed and which are light, which makes it hard to
start big assignments early.

The result is last-minute work, missed deadlines, and the stress of
never being sure that nothing has been forgotten.

# Initial requirements
A small command-line program, plan, that keeps all tasks in one file and
shows them in the terminal, sorted by urgency, with overdue and upcoming
items clearly highlighted.

- R1 Add a task. The user can add a task with a title and an optional
  due date, for example `plan add "CSC299 final" --due 2026-11-22`.
  Each task gets a number so it can be referred to later.
- R2 List tasks by urgency. `plan list` shows all tasks in this order:
  overdue first, then upcoming by soonest due date, then tasks with no
  date, then completed tasks.
- R3 Mark a task done. `plan done 4` marks task #4 as completed. It
  stays in the list but is shown as done.
- R4 Show a month view. `plan month` prints a calendar grid of the
  current month, marking days that have tasks due and days with overdue
  tasks.
- R5 Save tasks between runs. Tasks are stored in a `tasks.json` file,
  so they are still there the next time the program runs.
- R6 Make urgency stand out visually. Using colors and symbols in the
  terminal, overdue tasks are shown in red with a ⚠ symbol, tasks due
  within 3 days are highlighted, and done tasks are dimmed with a ✔.
