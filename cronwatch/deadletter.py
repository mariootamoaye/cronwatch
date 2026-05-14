"""Dead-letter queue: persist alerts that failed to send for later retry."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_DEFAULT_PATH = Path("~/.cronwatch/deadletter.json").expanduser()


@dataclass
class DeadLetterEntry:
    job_name: str
    alert_type: str  # "email" | "webhook"
    payload: dict
    error: str
    queued_at: str  # ISO-8601
    attempts: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "DeadLetterEntry":
        return DeadLetterEntry(
            job_name=d["job_name"],
            alert_type=d["alert_type"],
            payload=d["payload"],
            error=d["error"],
            queued_at=d["queued_at"],
            attempts=d.get("attempts", 1),
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return json.load(fh)


def _save_raw(entries: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(entries, fh, indent=2)


def enqueue(
    job_name: str,
    alert_type: str,
    payload: dict,
    error: str,
    path: Path = _DEFAULT_PATH,
) -> DeadLetterEntry:
    """Add a failed alert to the dead-letter queue."""
    entry = DeadLetterEntry(
        job_name=job_name,
        alert_type=alert_type,
        payload=payload,
        error=error,
        queued_at=datetime.now(timezone.utc).isoformat(),
    )
    raw = _load_raw(path)
    raw.append(entry.to_dict())
    _save_raw(raw, path)
    return entry


def list_entries(path: Path = _DEFAULT_PATH) -> List[DeadLetterEntry]:
    """Return all queued dead-letter entries."""
    return [DeadLetterEntry.from_dict(d) for d in _load_raw(path)]


def remove_entry(job_name: str, queued_at: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove a single entry by job_name + queued_at. Returns True if removed."""
    raw = _load_raw(path)
    filtered = [d for d in raw if not (d["job_name"] == job_name and d["queued_at"] == queued_at)]
    if len(filtered) == len(raw):
        return False
    _save_raw(filtered, path)
    return True


def clear(path: Path = _DEFAULT_PATH) -> int:
    """Remove all entries. Returns count removed."""
    raw = _load_raw(path)
    count = len(raw)
    _save_raw([], path)
    return count
