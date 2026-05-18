"""Job execution quota tracking — limit how many times a job may run in a window."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class QuotaEntry:
    job_name: str
    ran_at: str  # ISO-8601

    def to_dict(self) -> dict:
        return {"job_name": self.job_name, "ran_at": self.ran_at}

    @staticmethod
    def from_dict(d: dict) -> "QuotaEntry":
        return QuotaEntry(job_name=d["job_name"], ran_at=d["ran_at"])

    def dt(self) -> datetime:
        return datetime.fromisoformat(self.ran_at)


@dataclass
class QuotaResult:
    job_name: str
    limit: int
    window_hours: int
    count: int
    exceeded: bool

    def __str__(self) -> str:
        status = "EXCEEDED" if self.exceeded else "ok"
        return (
            f"{self.job_name}: {self.count}/{self.limit} runs "
            f"in last {self.window_hours}h [{status}]"
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_run(job_name: str, quota_file: Path) -> QuotaEntry:
    """Append a run timestamp for *job_name* to *quota_file*."""
    entry = QuotaEntry(job_name=job_name, ran_at=_now().isoformat())
    raw = _load_raw(quota_file)
    raw.append(entry.to_dict())
    _save_raw(quota_file, raw)
    return entry


def check_quota(
    job_name: str,
    limit: int,
    window_hours: int,
    quota_file: Path,
) -> QuotaResult:
    """Return a QuotaResult indicating whether *job_name* has exceeded its quota."""
    cutoff = _now() - timedelta(hours=window_hours)
    raw = _load_raw(quota_file)
    entries = [
        QuotaEntry.from_dict(r)
        for r in raw
        if r.get("job_name") == job_name
    ]
    recent = [e for e in entries if e.dt() >= cutoff]
    count = len(recent)
    return QuotaResult(
        job_name=job_name,
        limit=limit,
        window_hours=window_hours,
        count=count,
        exceeded=count > limit,
    )
