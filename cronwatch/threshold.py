"""Threshold alerting: fire an alert when a metric crosses a configured limit."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.history import HistoryEntry, load_history


@dataclass
class ThresholdResult:
    job_name: str
    metric: str          # 'failure_rate' | 'avg_duration' | 'max_duration'
    value: float
    limit: float
    breached: bool

    def __str__(self) -> str:
        status = "BREACHED" if self.breached else "ok"
        return (
            f"{self.job_name} [{self.metric}] "
            f"value={self.value:.2f} limit={self.limit:.2f} -> {status}"
        )


@dataclass
class ThresholdReport:
    results: List[ThresholdResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(not r.breached for r in self.results)

    @property
    def breached(self) -> List[ThresholdResult]:
        return [r for r in self.results if r.breached]


def _failure_rate(entries: List[HistoryEntry]) -> float:
    if not entries:
        return 0.0
    failed = sum(1 for e in entries if e.exit_code != 0)
    return failed / len(entries)


def _avg_duration(entries: List[HistoryEntry]) -> float:
    durations = [e.duration_seconds for e in entries if e.duration_seconds is not None]
    if not durations:
        return 0.0
    return sum(durations) / len(durations)


def _max_duration(entries: List[HistoryEntry]) -> float:
    durations = [e.duration_seconds for e in entries if e.duration_seconds is not None]
    return max(durations, default=0.0)


_METRIC_FN = {
    "failure_rate": _failure_rate,
    "avg_duration": _avg_duration,
    "max_duration": _max_duration,
}


def check_threshold(
    job_name: str,
    metric: str,
    limit: float,
    history_path: str,
    window: int = 10,
) -> ThresholdResult:
    """Check whether *metric* for *job_name* exceeds *limit*.

    Args:
        job_name:     Name of the cron job.
        metric:       One of 'failure_rate', 'avg_duration', 'max_duration'.
        limit:        Numeric limit; breach when value > limit.
        history_path: Path to the job's history JSON file.
        window:       Number of most-recent entries to consider.
    """
    if metric not in _METRIC_FN:
        raise ValueError(f"Unknown metric '{metric}'. Choose from {list(_METRIC_FN)}.")

    entries = load_history(history_path)
    recent = entries[-window:] if len(entries) > window else entries
    value = _METRIC_FN[metric](recent)
    return ThresholdResult(
        job_name=job_name,
        metric=metric,
        value=value,
        limit=limit,
        breached=value > limit,
    )
