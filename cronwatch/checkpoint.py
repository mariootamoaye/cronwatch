"""Checkpoint support — record and query named progress markers for long-running jobs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CheckpointEntry:
    job: str
    name: str
    timestamp: str
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CheckpointEntry":
        return cls(
            job=d["job"],
            name=d["name"],
            timestamp=d["timestamp"],
            note=d.get("note"),
        )

    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.timestamp)


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return json.load(fh)


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(entries, fh, indent=2)


def record_checkpoint(path: Path, job: str, name: str, note: Optional[str] = None) -> CheckpointEntry:
    """Append a checkpoint marker for *job* and return the entry."""
    entry = CheckpointEntry(job=job, name=name, timestamp=_now_iso(), note=note)
    raw = _load_raw(path)
    raw.append(entry.to_dict())
    _save_raw(path, raw)
    return entry


def list_checkpoints(path: Path, job: Optional[str] = None) -> List[CheckpointEntry]:
    """Return all checkpoints, optionally filtered to a single job."""
    entries = [CheckpointEntry.from_dict(d) for d in _load_raw(path)]
    if job is not None:
        entries = [e for e in entries if e.job == job]
    return entries


def last_checkpoint(path: Path, job: str) -> Optional[CheckpointEntry]:
    """Return the most recent checkpoint for *job*, or None."""
    entries = list_checkpoints(path, job=job)
    return entries[-1] if entries else None


def clear_checkpoints(path: Path, job: str) -> int:
    """Remove all checkpoints for *job*. Returns the number removed."""
    raw = _load_raw(path)
    kept = [d for d in raw if d["job"] != job]
    _save_raw(path, kept)
    return len(raw) - len(kept)
