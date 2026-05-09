"""Detect and report schedule jitter — jobs running significantly earlier or later than expected."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from cronwatch.history import HistoryEntry, load_history


@dataclass
class JitterEntry:
    job_name: str
    expected_interval_seconds: float
    actual_interval_seconds: float
    deviation_seconds: float
    timestamp: datetime

    @property
    def is_late(self) -> bool:
        return self.deviation_seconds > 0

    @property
    def is_early(self) -> bool:
        return self.deviation_seconds < 0


@dataclass
class JitterReport:
    entries: List[JitterEntry] = field(default_factory=list)
    threshold_seconds: float = 60.0

    @property
    def all_ok(self) -> bool:
        return all(abs(e.deviation_seconds) <= self.threshold_seconds for e in self.entries)

    @property
    def violations(self) -> List[JitterEntry]:
        return [e for e in self.entries if abs(e.deviation_seconds) > self.threshold_seconds]


def _compute_jitter(
    entries: List[HistoryEntry],
    expected_interval_seconds: float,
) -> List[JitterEntry]:
    """Given a sorted list of history entries, compute jitter relative to expected interval."""
    jitter: List[JitterEntry] = []
    sorted_entries = sorted(entries, key=lambda e: e.started_at)
    for i in range(1, len(sorted_entries)):
        prev = sorted_entries[i - 1]
        curr = sorted_entries[i]
        actual = (curr.started_at - prev.started_at).total_seconds()
        deviation = actual - expected_interval_seconds
        jitter.append(
            JitterEntry(
                job_name=curr.job_name,
                expected_interval_seconds=expected_interval_seconds,
                actual_interval_seconds=actual,
                deviation_seconds=deviation,
                timestamp=curr.started_at,
            )
        )
    return jitter


def check_jitter(
    history_path: str,
    job_name: str,
    expected_interval_seconds: float,
    threshold_seconds: float = 60.0,
    lookback: Optional[timedelta] = None,
) -> JitterReport:
    """Load history for a job and return a JitterReport."""
    all_entries = load_history(history_path)
    job_entries = [e for e in all_entries if e.job_name == job_name]

    if lookback is not None:
        cutoff = datetime.utcnow() - lookback
        job_entries = [e for e in job_entries if e.started_at >= cutoff]

    entries = _compute_jitter(job_entries, expected_interval_seconds)
    return JitterReport(entries=entries, threshold_seconds=threshold_seconds)
