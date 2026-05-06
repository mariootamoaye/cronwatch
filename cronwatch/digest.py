"""Periodic digest: aggregate history entries into a summary email."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from cronwatch.history import HistoryEntry, load_recent


@dataclass
class DigestStats:
    job_name: str
    total_runs: int = 0
    failures: int = 0
    timeouts: int = 0
    avg_duration: float = 0.0
    last_run: datetime | None = None

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 100.0
        ok = self.total_runs - self.failures - self.timeouts
        return round(ok / self.total_runs * 100, 1)


@dataclass
class Digest:
    period_hours: int
    generated_at: datetime = field(default_factory=datetime.utcnow)
    stats: List[DigestStats] = field(default_factory=list)

    @property
    def all_healthy(self) -> bool:
        return all(s.failures == 0 and s.timeouts == 0 for s in self.stats)


def _aggregate(entries: List[HistoryEntry]) -> List[DigestStats]:
    """Group entries by job name and compute per-job stats."""
    by_job: dict[str, List[HistoryEntry]] = {}
    for e in entries:
        by_job.setdefault(e.job_name, []).append(e)

    result: List[DigestStats] = []
    for name, job_entries in sorted(by_job.items()):
        durations = [e.duration for e in job_entries if e.duration is not None]
        stats = DigestStats(
            job_name=name,
            total_runs=len(job_entries),
            failures=sum(1 for e in job_entries if e.exit_code != 0 and not e.timed_out),
            timeouts=sum(1 for e in job_entries if e.timed_out),
            avg_duration=round(sum(durations) / len(durations), 2) if durations else 0.0,
            last_run=max((e.started_at for e in job_entries), default=None),
        )
        result.append(stats)
    return result


def build_digest(history_path: str, period_hours: int = 24) -> Digest:
    """Load history for the last *period_hours* and build a Digest."""
    since = datetime.utcnow() - timedelta(hours=period_hours)
    entries = load_recent(history_path, since=since)
    return Digest(
        period_hours=period_hours,
        stats=_aggregate(entries),
    )
