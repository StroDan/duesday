"""Load and save tasks as JSON."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path

from .tasks import Task


class StorageError(Exception):
    """The task file exists but cannot be read or written."""


def default_path() -> Path:
    return Path.home() / ".duesday" / "tasks.json"


def _task_from_dict(raw: object) -> Task:
    if not isinstance(raw, dict):
        raise ValueError("task entry is not an object")
    task_id, title, due, done = raw["id"], raw["title"], raw.get("due"), raw.get("done", False)
    if type(task_id) is not int or task_id < 1:
        raise ValueError(f"bad task id {task_id!r}")
    if not isinstance(title, str) or not isinstance(done, bool):
        raise ValueError(f"bad title or done flag in task #{task_id}")
    if due is not None and not isinstance(due, str):
        raise ValueError(f"bad due date in task #{task_id}")
    return Task(task_id, title, date.fromisoformat(due) if due else None, done)


def load_tasks(path: Path) -> list[Task]:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as e:
        raise StorageError(f"cannot read {path}: {e.strerror}") from None
    try:
        data = json.loads(text)
        if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
            raise ValueError('expected an object with a "tasks" list')
        return [_task_from_dict(raw) for raw in data["tasks"]]
    except (ValueError, KeyError, TypeError) as e:
        raise StorageError(f"{path} is not a valid task file ({e}); fix or move it") from None


def save_tasks(path: Path, tasks: list[Task]) -> None:
    path = Path(path)
    data = {
        "tasks": [
            {"id": t.id, "title": t.title, "due": t.due.isoformat() if t.due else None, "done": t.done}
            for t in tasks
        ]
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tasks-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
    except OSError as e:
        raise StorageError(f"cannot write {path}: {e.strerror}") from None
