"""Forecast next expected run time for a job based on history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import List, Optional

from cronwatch.history import load_entries, HistoryEntry


@dataclass
class ForecastResult:
    job_name: str
    last_run: Optional[datetime]
    avg_interval_seconds: Optional[float]
    next_expected: Optional[datetime]
    confidence: str  # "high" | "low" | "none"

    @property
    def ok(self) -> bool:
        return self.next_expected is not None


def _intervals(entries: List[HistoryEntry]) -> List[float]:
    """Return list of seconds between consecutive runs (ascending order)."""
    timestamps = sorted(e.started_at for e in entries)
    return [
        (timestamps[i + 1] - timestamps[i]).total_seconds()
        for i in range(len(timestamps) - 1)
    ]


def forecast_job(
    job_name: str,
    history_path: Path,
    min_samples: int = 3,
) -> ForecastResult:
    """Compute the forecast for *job_name* using stored history."""
    entries = [e for e in load_entries(history_path) if e.job_name == job_name]

    if not entries:
        return ForecastResult(
            job_name=job_name,
            last_run=None,
            avg_interval_seconds=None,
            next_expected=None,
            confidence="none",
        )

    last_run = max(e.started_at for e in entries)
    intervals = _intervals(entries)

    if len(intervals) < min_samples:
        return ForecastResult(
            job_name=job_name,
            last_run=last_run,
            avg_interval_seconds=None,
            next_expected=None,
            confidence="low",
        )

    avg = mean(intervals)
    next_expected = last_run + timedelta(seconds=avg)
    confidence = "high" if len(intervals) >= 10 else "low"

    return ForecastResult(
        job_name=job_name,
        last_run=last_run,
        avg_interval_seconds=avg,
        next_expected=next_expected,
        confidence=confidence,
    )
