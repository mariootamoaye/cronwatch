"""Persistent per-job run history stored as newline-delimited JSON."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class HistoryEntry:
    job_name: str
    started_at: datetime
    duration_seconds: float
    exit_code: int
    timed_out: bool
    note: str = ""


def from_dict(d: Dict[str, Any]) -> HistoryEntry:
    return HistoryEntry(
        job_name=d["job_name"],
        started_at=datetime.fromisoformat(d["started_at"]),
        duration_seconds=float(d["duration_seconds"]),
        exit_code=int(d["exit_code"]),
        timed_out=bool(d["timed_out"]),
        note=d.get("note", ""),
    )


def _load_raw(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _save_raw(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def record(path: str, entry: HistoryEntry) -> None:
    rows = _load_raw(path)
    rows.append(
        {
            "job_name": entry.job_name,
            "started_at": entry.started_at.isoformat(),
            "duration_seconds": entry.duration_seconds,
            "exit_code": entry.exit_code,
            "timed_out": entry.timed_out,
            "note": entry.note,
        }
    )
    _save_raw(path, rows)


def load(path: str) -> List[HistoryEntry]:
    return [from_dict(d) for d in _load_raw(path)]


def recent(path: str, job_name: str, limit: int = 10) -> List[HistoryEntry]:
    """Return up to *limit* most-recent entries for *job_name*."""
    entries = [
        e for e in load(path) if e.job_name == job_name
    ]
    return entries[-limit:]
