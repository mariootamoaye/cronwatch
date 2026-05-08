"""Snooze support — suppress alerts for a job until a given time."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_PATH = Path(".cronwatch_snooze.json")


@dataclass(frozen=True)
class SnoozeEntry:
    job_name: str
    until: datetime

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now < self.until


def _load_raw(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_raw(data: Dict[str, str], path: Path) -> None:
    path.write_text(json.dumps(data, indent=2))


def snooze_job(job_name: str, until: datetime, path: Path = _DEFAULT_PATH) -> None:
    """Record a snooze for *job_name* until *until* (must be tz-aware UTC)."""
    raw = _load_raw(path)
    raw[job_name] = until.isoformat()
    _save_raw(raw, path)


def clear_snooze(job_name: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove an existing snooze.  Returns True if one was present."""
    raw = _load_raw(path)
    if job_name not in raw:
        return False
    del raw[job_name]
    _save_raw(raw, path)
    return True


def is_snoozed(
    job_name: str,
    now: Optional[datetime] = None,
    path: Path = _DEFAULT_PATH,
) -> bool:
    """Return True when *job_name* has an active snooze."""
    raw = _load_raw(path)
    if job_name not in raw:
        return False
    until = datetime.fromisoformat(raw[job_name])
    entry = SnoozeEntry(job_name=job_name, until=until)
    return entry.is_active(now)


def load_all(path: Path = _DEFAULT_PATH) -> Dict[str, SnoozeEntry]:
    """Return all stored snooze entries (active or expired)."""
    raw = _load_raw(path)
    return {
        name: SnoozeEntry(job_name=name, until=datetime.fromisoformat(ts))
        for name, ts in raw.items()
    }
