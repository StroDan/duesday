# duesday: `plan`

A small command-line deadline tracker for students. It keeps every task
(course deadlines, work shifts, errands) in one file and shows them in the
terminal sorted by urgency: overdue tasks in red with ⚠, tasks due within
3 days highlighted, done tasks dimmed with ✔. A month calendar shows which
days are busy and which have overdue work.

Tasks are saved in `~/.duesday/tasks.json`, so you see the same list from any folder.

## Run it

From the repo folder (needs Python 3.12; the first run creates `.venv` and
installs dependencies automatically):

```bash
./plan                                       # interactive menu (see below)
./plan add "CSC299 final" --due 2026-11-22   # add a task (due date optional)
./plan list                                  # all tasks, most urgent first
./plan done 4                                # mark task #4 done
./plan month                                 # calendar of the current month
./plan --help
```

`--file PATH` uses a different task file instead of `~/.duesday/tasks.json`.

### The menu

Run `./plan` with no command to open a numbered menu: `1` add, `2` list,
`3` done, `4` month, `q` quit. It asks for what it needs one step at a time
(press Enter to skip the due date). After each action it shows the matching
command as a tip, e.g. `Tip: ./plan add "Essay" --due 2026-11-20`, so you can
learn the shortcuts. Ctrl+C also quits. The menu clears the screen each time
it is shown; the normal commands never clear it.

In a script or pipe (no terminal), `./plan` with no command just prints the
usage line and exits instead of waiting for input.

Works in macOS/Linux terminals and in Git Bash on Windows.

## Run the tests

After `./plan` has run once (so `.venv` exists):

```bash
.venv/bin/python -m pytest            # macOS / Linux
.venv/Scripts/python -m pytest        # Git Bash on Windows
```

See `problem.md` for the requirements and `spec.md` for the exact behavior.
