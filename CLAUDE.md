# CLAUDE.md

CSC299 final project: `plan`, a command-line deadline tracker.

- `problem.md` is the source of truth; `spec.md` turns it into exact behavior.
  If they disagree or something is unclear, ask before coding.
- Python 3.12, `rich` for output, `pytest` for tests. No API keys, logins, or paid services.
- Run: `./plan <command>`. Tests: `.venv/bin/python -m pytest` (after `./plan` has created `.venv`).
- Keep logic (`duesday/tasks.py`, `duesday/storage.py`) free of printing and of the clock;
  "today" is always a parameter. Only `duesday/cli.py` reads the date and prints.
- Tests must never touch `~/.duesday`; use `--file` / `tmp_path`.
- Every test name starts with the requirement ID it checks, e.g. `test_R2_...`.
- Commits: small, message says what changed and why. Never amend, never push.
