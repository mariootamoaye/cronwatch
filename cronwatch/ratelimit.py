"""Rate limiting for alerts — suppresses repeated alerts within a cooldown window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class RateLimitEntry:
    job_name: str
    last_alerted_at: float  # Unix timestamp

    def is_cooling_down(self, cooldown_seconds: int, now: Optional[float] = None) -> bool:
        if now is None:
            now = time.time()
        return (now - self.last_alerted_at) < cooldown_seconds


def _load_raw(path: Path) -> Dict[str, float]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_raw(path: Path, data: Dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def record_alert(path: Path, job_name: str, now: Optional[float] = None) -> None:
    """Record that an alert was sent for *job_name* right now."""
    data = _load_raw(path)
    data[job_name] = now if now is not None else time.time()
    _save_raw(path, data)


def is_rate_limited(
    path: Path,
    job_name: str,
    cooldown_seconds: int,
    now: Optional[float] = None,
) -> bool:
    """Return True if an alert for *job_name* was sent within *cooldown_seconds*."""
    if cooldown_seconds <= 0:
        return False
    data = _load_raw(path)
    if job_name not in data:
        return False
    entry = RateLimitEntry(job_name=job_name, last_alerted_at=data[job_name])
    return entry.is_cooling_down(cooldown_seconds, now=now)


def clear_rate_limit(path: Path, job_name: str) -> bool:
    """Remove the rate-limit record for *job_name*. Returns True if it existed."""
    data = _load_raw(path)
    if job_name not in data:
        return False
    del data[job_name]
    _save_raw(path, data)
    return True


def seconds_until_clear(
    path: Path,
    job_name: str,
    cooldown_seconds: int,
    now: Optional[float] = None,
) -> Optional[float]:
    """Return how many seconds remain in the cooldown for *job_name*.

    Returns ``None`` if *job_name* has no rate-limit record or is not currently
    cooling down.  Returns ``0.0`` if the cooldown has just expired.
    """
    if cooldown_seconds <= 0:
        return None
    data = _load_raw(path)
    if job_name not in data:
        return None
    if now is None:
        now = time.time()
    remaining = cooldown_seconds - (now - data[job_name])
    return max(remaining, 0.0) if remaining > 0 else None
