"""Baseline duration tracking: record expected job durations and detect anomalies."""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class BaselineStats:
    job_name: str
    sample_count: int
    mean_seconds: float
    stddev_seconds: float

    @property
    def upper_bound(self) -> float:
        """Mean + 2 standard deviations."""
        return self.mean_seconds + 2.0 * self.stddev_seconds

    def is_anomalous(self, duration_seconds: float) -> bool:
        if self.sample_count < 3:
            return False
        return duration_seconds > self.upper_bound


@dataclass
class BaselineResult:
    job_name: str
    duration_seconds: float
    stats: Optional[BaselineStats]
    anomalous: bool

    @property
    def ok(self) -> bool:
        return not self.anomalous


def _load_raw(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_raw(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def record_duration(job_name: str, duration_seconds: float, path: Path, max_samples: int = 50) -> None:
    """Append a duration sample for a job, keeping at most *max_samples* entries."""
    data = _load_raw(path)
    samples: List[float] = data.get(job_name, [])
    samples.append(duration_seconds)
    if len(samples) > max_samples:
        samples = samples[-max_samples:]
    data[job_name] = samples
    _save_raw(path, data)


def compute_stats(job_name: str, path: Path) -> Optional[BaselineStats]:
    """Return baseline statistics for *job_name*, or None if insufficient data."""
    data = _load_raw(path)
    samples: List[float] = data.get(job_name, [])
    if len(samples) < 2:
        return None
    return BaselineStats(
        job_name=job_name,
        sample_count=len(samples),
        mean_seconds=statistics.mean(samples),
        stddev_seconds=statistics.pstdev(samples),
    )


def check_baseline(job_name: str, duration_seconds: float, path: Path) -> BaselineResult:
    """Check whether *duration_seconds* is anomalous relative to recorded baseline."""
    stats = compute_stats(job_name, path)
    anomalous = stats.is_anomalous(duration_seconds) if stats is not None else False
    return BaselineResult(
        job_name=job_name,
        duration_seconds=duration_seconds,
        stats=stats,
        anomalous=anomalous,
    )
