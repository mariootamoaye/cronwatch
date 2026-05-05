"""Persistent job run history using a simple JSON file store."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_PATH = Path(os.environ.get("CRONWATCH_HISTORY", "~/.cronwatch_history.json")).expanduser()
MAX_ENTRIES_PER_JOB = 100


@dataclass
class HistoryEntry:
    job_name: str
    started_at: str          # ISO-8601
    duration_seconds: float
    exit_code: int
    timed_out: bool
    success: bool

    @staticmethod
    def from_dict(d: dict) -> "HistoryEntry":
        return HistoryEntry(
            job_name=d["job_name"],
            started_at=d["started_at"],
            duration_seconds=d["duration_seconds"],
            exit_code=d["exit_code"],
            timed_out=d["timed_out"],
            success=d["success"],
        )


def _load_raw(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open() as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_raw(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def record(entry: HistoryEntry, path: Path = DEFAULT_HISTORY_PATH) -> None:
    """Append *entry* to the history file, pruning old entries."""
    data = _load_raw(path)
    entries = data.get(entry.job_name, [])
    entries.append(asdict(entry))
    entries = entries[-MAX_ENTRIES_PER_JOB:]
    data[entry.job_name] = entries
    _save_raw(path, data)


def get_entries(job_name: str, path: Path = DEFAULT_HISTORY_PATH) -> List[HistoryEntry]:
    """Return all stored history entries for *job_name*."""
    data = _load_raw(path)
    return [HistoryEntry.from_dict(d) for d in data.get(job_name, [])]


def last_entry(job_name: str, path: Path = DEFAULT_HISTORY_PATH) -> Optional[HistoryEntry]:
    """Return the most recent history entry for *job_name*, or None."""
    entries = get_entries(job_name, path)
    return entries[-1] if entries else None
