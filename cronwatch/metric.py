"""Per-job runtime metric tracking: record and retrieve duration samples."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class MetricSample:
    job_name: str
    timestamp: str
    duration_seconds: float
    exit_code: int

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MetricSample":
        return cls(
            job_name=d["job_name"],
            timestamp=d["timestamp"],
            duration_seconds=float(d["duration_seconds"]),
            exit_code=int(d["exit_code"]),
        )


@dataclass
class MetricSummary:
    job_name: str
    sample_count: int
    min_duration: float
    max_duration: float
    avg_duration: float
    p95_duration: float


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def record_metric(path: Path, sample: MetricSample) -> None:
    entries = _load_raw(path)
    entries.append(sample.to_dict())
    _save_raw(path, entries)


def list_metrics(path: Path, job_name: Optional[str] = None) -> List[MetricSample]:
    entries = _load_raw(path)
    samples = [MetricSample.from_dict(e) for e in entries]
    if job_name is not None:
        samples = [s for s in samples if s.job_name == job_name]
    return samples


def summarize_metrics(path: Path, job_name: str) -> Optional[MetricSummary]:
    samples = list_metrics(path, job_name)
    if not samples:
        return None
    durations = sorted(s.duration_seconds for s in samples)
    n = len(durations)
    p95_idx = max(0, int(n * 0.95) - 1)
    return MetricSummary(
        job_name=job_name,
        sample_count=n,
        min_duration=durations[0],
        max_duration=durations[-1],
        avg_duration=sum(durations) / n,
        p95_duration=durations[p95_idx],
    )
