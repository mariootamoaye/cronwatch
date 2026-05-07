"""Heartbeat check: detect jobs that have not run within their expected interval."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from cronwatch.history import HistoryEntry, recent


@dataclass(frozen=True)
class HeartbeatResult:
    job_name: str
    last_run: Optional[datetime]
    expected_interval_hours: float
    is_late: bool
    hours_overdue: float


@dataclass(frozen=True)
class HeartbeatReport:
    results: List[HeartbeatResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return not any(r.is_late for r in self.results)

    @property
    def late_jobs(self) -> List[HeartbeatResult]:
        return [r for r in self.results if r.is_late]


def check_heartbeat(
    job_name: str,
    history_path: str,
    expected_interval_hours: float,
    now: Optional[datetime] = None,
) -> HeartbeatResult:
    """Return a HeartbeatResult indicating whether *job_name* is overdue."""
    if now is None:
        now = datetime.now(tz=timezone.utc)

    entries: List[HistoryEntry] = recent(history_path, job_name, limit=1)
    last_run: Optional[datetime] = entries[0].started_at if entries else None

    if last_run is None:
        is_late = True
        hours_overdue = expected_interval_hours
    else:
        deadline = last_run + timedelta(hours=expected_interval_hours)
        delta = (now - deadline).total_seconds() / 3600
        is_late = delta > 0
        hours_overdue = max(0.0, delta)

    return HeartbeatResult(
        job_name=job_name,
        last_run=last_run,
        expected_interval_hours=expected_interval_hours,
        is_late=is_late,
        hours_overdue=round(hours_overdue, 2),
    )


def build_heartbeat_report(
    job_intervals: Dict[str, float],
    history_dir: str,
    now: Optional[datetime] = None,
) -> HeartbeatReport:
    """Check heartbeats for all jobs in *job_intervals* and return a report."""
    import os

    results = []
    for job_name, interval_hours in job_intervals.items():
        history_path = os.path.join(history_dir, f"{job_name}.json")
        result = check_heartbeat(job_name, history_path, interval_hours, now=now)
        results.append(result)
    return HeartbeatReport(results=results)
