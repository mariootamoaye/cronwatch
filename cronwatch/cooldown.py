"""Cooldown tracking: suppress repeated alerts for a job within a quiet window."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


@dataclass
class CooldownEntry:
    job_name: str
    last_alerted: datetime
    window_seconds: int

    def is_cooling_down(self, at: Optional[datetime] = None) -> bool:
        """Return True if the job is still within its cooldown window."""
        reference = at or _now()
        expiry = self.last_alerted + timedelta(seconds=self.window_seconds)
        return reference < expiry

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "last_alerted": self.last_alerted.isoformat(),
            "window_seconds": self.window_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CooldownEntry":
        return cls(
            job_name=data["job_name"],
            last_alerted=datetime.fromisoformat(data["last_alerted"]),
            window_seconds=int(data["window_seconds"]),
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_alert(job_name: str, window_seconds: int, path: Path) -> CooldownEntry:
    """Record that an alert was just sent for *job_name*."""
    raw = _load_raw(path)
    entries: Dict[str, dict] = {r["job_name"]: r for r in raw}
    entry = CooldownEntry(
        job_name=job_name,
        last_alerted=_now(),
        window_seconds=window_seconds,
    )
    entries[job_name] = entry.to_dict()
    _save_raw(path, list(entries.values()))
    return entry


def is_cooling_down(job_name: str, path: Path, at: Optional[datetime] = None) -> bool:
    """Return True if *job_name* is currently in a cooldown period."""
    raw = _load_raw(path)
    for r in raw:
        if r["job_name"] == job_name:
            return CooldownEntry.from_dict(r).is_cooling_down(at=at)
    return False


def clear_cooldown(job_name: str, path: Path) -> bool:
    """Remove the cooldown entry for *job_name*. Returns True if an entry existed."""
    raw = _load_raw(path)
    filtered = [r for r in raw if r["job_name"] != job_name]
    if len(filtered) == len(raw):
        return False
    _save_raw(path, filtered)
    return True
