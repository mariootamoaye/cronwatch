"""Persist and retrieve job run history as newline-delimited JSON."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

_DT_FMT = "%Y-%m-%dT%H:%M:%S"


@dataclass
class HistoryEntry:
    job_name: str
    started_at: datetime
    exit_code: int
    duration: Optional[float] = None
    timed_out: bool = False
    stderr_snippet: str = ""


def from_dict(d: dict) -> HistoryEntry:
    return HistoryEntry(
        job_name=d["job_name"],
        started_at=datetime.strptime(d["started_at"], _DT_FMT),
        exit_code=d["exit_code"],
        duration=d.get("duration"),
        timed_out=d.get("timed_out", False),
        stderr_snippet=d.get("stderr_snippet", ""),
    )


def _load_raw(path: str) -> List[dict]:
    p = Path(path)
    if not p.exists():
        return []
    rows = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _save_raw(path: str, rows: List[dict]) -> None:
    Path(path).write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def record(path: str, entry: HistoryEntry) -> None:
    rows = _load_raw(path)
    d = asdict(entry)
    d["started_at"] = entry.started_at.strftime(_DT_FMT)
    rows.append(d)
    _save_raw(path, rows)


def load_all(path: str) -> List[HistoryEntry]:
    return [from_dict(r) for r in _load_raw(path)]


def load_recent(path: str, since: datetime) -> List[HistoryEntry]:
    """Return entries whose started_at is >= *since*."""
    return [e for e in load_all(path) if e.started_at >= since]
