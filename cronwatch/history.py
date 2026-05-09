"""Persistent run history for cron jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class HistoryEntry:
    job_name: str
    started_at: str          # ISO-8601
    duration_seconds: float
    exit_code: int
    timed_out: bool
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def from_dict(d: Dict[str, Any]) -> HistoryEntry:
    return HistoryEntry(
        job_name=d["job_name"],
        started_at=d["started_at"],
        duration_seconds=float(d["duration_seconds"]),
        exit_code=int(d["exit_code"]),
        timed_out=bool(d["timed_out"]),
        note=d.get("note", ""),
    )


def _load_raw(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open() as fh:
        return json.load(fh)


def _save_raw(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(entries, fh, indent=2)


def record(path: Path, entry: HistoryEntry) -> None:
    """Append *entry* to the history file at *path*."""
    raw = _load_raw(path)
    raw.append(entry.to_dict())
    _save_raw(path, raw)


def load_all(path: Path, job_name: Optional[str] = None) -> List[HistoryEntry]:
    """Return all entries, optionally filtered by *job_name*, newest first."""
    raw = _load_raw(path)
    entries = [from_dict(r) for r in raw]
    if job_name is not None:
        entries = [e for e in entries if e.job_name == job_name]
    entries.sort(key=lambda e: e.started_at, reverse=True)
    return entries


def load_recent(
    path: Path, job_name: str, limit: int = 10
) -> List[HistoryEntry]:
    """Return up to *limit* most-recent entries for *job_name*."""
    return load_all(path, job_name)[:limit]
