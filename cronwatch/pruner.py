"""Orchestrates retention pruning across all job history files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from cronwatch.config import RetentionConfig
from cronwatch.retention import RetentionResult, prune_by_age, prune_by_count


@dataclass
class PruneReport:
    job_name: str
    age_result: RetentionResult | None
    count_result: RetentionResult | None

    @property
    def total_removed(self) -> int:
        age = self.age_result.removed if self.age_result else 0
        count = self.count_result.removed if self.count_result else 0
        return age + count


@dataclass
class PrunerResult:
    reports: List[PruneReport] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return sum(r.total_removed for r in self.reports)

    @property
    def jobs_pruned(self) -> int:
        return sum(1 for r in self.reports if r.total_removed > 0)


def prune_job(history_file: Path, retention: RetentionConfig) -> PruneReport:
    """Apply all configured retention rules to a single job's history file."""
    job_name = history_file.stem
    age_result = None
    count_result = None

    if retention.max_age_days is not None:
        age_result = prune_by_age(history_file, retention.max_age_days)

    if retention.max_entries is not None:
        count_result = prune_by_count(history_file, retention.max_entries)

    return PruneReport(job_name=job_name, age_result=age_result, count_result=count_result)


def run_pruner(history_dir: Path, retention: RetentionConfig) -> PrunerResult:
    """Run retention pruning for every job history file found in *history_dir*."""
    result = PrunerResult()

    if not history_dir.exists():
        return result

    for history_file in sorted(history_dir.glob("*.json")):
        report = prune_job(history_file, retention)
        result.reports.append(report)

    return result
