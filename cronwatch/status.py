"""Job status board: aggregates latest run per job from history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from cronwatch.history import HistoryEntry, load_recent


@dataclass
class JobStatus:
    job_name: str
    last_run: Optional[datetime]
    last_exit_code: Optional[int]
    last_duration: Optional[float]
    consecutive_failures: int

    @property
    def ok(self) -> bool:
        return self.last_exit_code == 0

    @property
    def never_run(self) -> bool:
        return self.last_run is None


@dataclass
class StatusBoard:
    jobs: List[JobStatus]

    @property
    def all_ok(self) -> bool:
        return all(j.ok for j in self.jobs if not j.never_run)

    @property
    def failing(self) -> List[JobStatus]:
        return [j for j in self.jobs if not j.never_run and not j.ok]


def _consecutive_failures(entries: List[HistoryEntry]) -> int:
    """Count failures from the most recent entry backwards."""
    count = 0
    for entry in reversed(entries):
        if entry.exit_code != 0:
            count += 1
        else:
            break
    return count


def build_status_board(history_dir: str, job_names: List[str]) -> StatusBoard:
    """Build a StatusBoard for the given job names using stored history."""
    statuses: List[JobStatus] = []

    for name in job_names:
        entries: List[HistoryEntry] = load_recent(history_dir, name, limit=50)

        if not entries:
            statuses.append(
                JobStatus(
                    job_name=name,
                    last_run=None,
                    last_exit_code=None,
                    last_duration=None,
                    consecutive_failures=0,
                )
            )
            continue

        latest = entries[-1]
        statuses.append(
            JobStatus(
                job_name=name,
                last_run=latest.timestamp,
                last_exit_code=latest.exit_code,
                last_duration=latest.duration,
                consecutive_failures=_consecutive_failures(entries),
            )
        )

    return StatusBoard(jobs=statuses)
