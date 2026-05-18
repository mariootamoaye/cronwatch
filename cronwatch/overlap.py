"""Detect overlapping (concurrent) job runs using lock files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class OverlapEntry:
    job_name: str
    pid: int
    started_at: str

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "pid": self.pid,
            "started_at": self.started_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OverlapEntry":
        return cls(
            job_name=data["job_name"],
            pid=data["pid"],
            started_at=data["started_at"],
        )


@dataclass
class OverlapResult:
    job_name: str
    overlapping: bool
    existing_entry: Optional[OverlapEntry] = None

    @property
    def ok(self) -> bool:
        return not self.overlapping

    def __str__(self) -> str:
        if self.ok:
            return f"{self.job_name}: no overlap detected"
        e = self.existing_entry
        return (
            f"{self.job_name}: already running (pid={e.pid}, "
            f"started={e.started_at})"
        )


def _lock_path(lock_dir: Path, job_name: str) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return lock_dir / f"{safe}.lock"


def acquire_lock(job_name: str, lock_dir: Path) -> OverlapResult:
    """Try to acquire a lock for *job_name*.

    Returns an OverlapResult indicating whether the job is already running.
    If no overlap is detected the lock file is written.
    """
    lock_dir.mkdir(parents=True, exist_ok=True)
    path = _lock_path(lock_dir, job_name)

    if path.exists():
        try:
            data = json.loads(path.read_text())
            entry = OverlapEntry.from_dict(data)
            # Check whether the recorded PID is still alive.
            try:
                os.kill(entry.pid, 0)
                return OverlapResult(job_name=job_name, overlapping=True, existing_entry=entry)
            except (ProcessLookupError, PermissionError):
                # Stale lock — process is gone.
                pass
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupt lock; treat as stale.

    entry = OverlapEntry(job_name=job_name, pid=os.getpid(), started_at=_now_iso())
    path.write_text(json.dumps(entry.to_dict()))
    return OverlapResult(job_name=job_name, overlapping=False, existing_entry=entry)


def release_lock(job_name: str, lock_dir: Path) -> bool:
    """Remove the lock file for *job_name*. Returns True if removed."""
    path = _lock_path(lock_dir, job_name)
    if path.exists():
        path.unlink()
        return True
    return False
