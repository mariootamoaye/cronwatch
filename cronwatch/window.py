"""Maintenance window support — suppress alerts during planned downtime."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_DEFAULT_PATH = Path("~/.cronwatch/windows.json").expanduser()


@dataclass
class WindowEntry:
    job: str
    start: str   # ISO-8601
    end: str     # ISO-8601
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if now is None:
            now = datetime.now(tz=timezone.utc)
        start_dt = datetime.fromisoformat(self.start)
        end_dt = datetime.fromisoformat(self.end)
        return start_dt <= now <= end_dt

    def to_dict(self) -> dict:
        return {
            "job": self.job,
            "start": self.start,
            "end": self.end,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WindowEntry":
        return cls(
            job=d["job"],
            start=d["start"],
            end=d["end"],
            reason=d.get("reason", ""),
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_raw(entries: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def add_window(job: str, start: str, end: str, reason: str = "",
               path: Path = _DEFAULT_PATH) -> WindowEntry:
    entry = WindowEntry(job=job, start=start, end=end, reason=reason)
    raw = _load_raw(path)
    raw.append(entry.to_dict())
    _save_raw(raw, path)
    return entry


def list_windows(path: Path = _DEFAULT_PATH) -> List[WindowEntry]:
    return [WindowEntry.from_dict(d) for d in _load_raw(path)]


def is_in_window(job: str, now: Optional[datetime] = None,
                 path: Path = _DEFAULT_PATH) -> bool:
    """Return True if *job* is currently inside an active maintenance window."""
    for entry in list_windows(path):
        if entry.job == job and entry.is_active(now):
            return True
    return False


def purge_expired(path: Path = _DEFAULT_PATH,
                  now: Optional[datetime] = None) -> int:
    """Remove windows whose end time is in the past. Returns count removed."""
    if now is None:
        now = datetime.now(tz=timezone.utc)
    entries = list_windows(path)
    active = [e for e in entries if datetime.fromisoformat(e.end) >= now]
    removed = len(entries) - len(active)
    _save_raw([e.to_dict() for e in active], path)
    return removed
