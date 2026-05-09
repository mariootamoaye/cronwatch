"""Escalation policy: re-alert if a job keeps failing across consecutive runs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from cronwatch.history import HistoryEntry, load_recent


@dataclass
class EscalationResult:
    job_name: str
    consecutive_failures: int
    should_escalate: bool
    threshold: int

    @property
    def ok(self) -> bool:
        return not self.should_escalate


def check_escalation(
    job_name: str,
    history_path: Path,
    threshold: int = 3,
) -> EscalationResult:
    """Return an EscalationResult indicating whether the job has failed
    *threshold* or more times in a row and should trigger an escalated alert."""
    if threshold <= 0:
        raise ValueError("threshold must be a positive integer")

    entries: List[HistoryEntry] = load_recent(history_path, job_name, limit=threshold)

    # Entries are returned newest-first; count leading failures.
    consecutive = 0
    for entry in entries:
        if entry.exit_code != 0 or entry.timed_out:
            consecutive += 1
        else:
            break

    should_escalate = consecutive >= threshold
    return EscalationResult(
        job_name=job_name,
        consecutive_failures=consecutive,
        should_escalate=should_escalate,
        threshold=threshold,
    )
