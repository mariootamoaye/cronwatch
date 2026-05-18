"""Replay failed jobs from the dead-letter queue."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwatch.deadletter import DeadLetterEntry, list_entries, remove_entry
from cronwatch.runner import JobResult, run_job
from cronwatch.config import JobConfig


@dataclass
class ReplayResult:
    job_name: str
    original_ts: str
    success: bool
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    error: str = ""

    def __str__(self) -> str:
        status = "ok" if self.success else "FAILED"
        return f"{self.job_name} [{self.original_ts}] -> {status} (exit={self.exit_code})"


@dataclass
class ReplayReport:
    results: List[ReplayResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(r.success for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return self.total - self.succeeded


def replay_job(entry: DeadLetterEntry, job_cfg: JobConfig) -> ReplayResult:
    """Re-run a single dead-letter entry using the current job config."""
    try:
        result: JobResult = run_job(job_cfg)
        return ReplayResult(
            job_name=entry.job_name,
            original_ts=entry.timestamp,
            success=result.success,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except Exception as exc:  # noqa: BLE001
        return ReplayResult(
            job_name=entry.job_name,
            original_ts=entry.timestamp,
            success=False,
            exit_code=-1,
            error=str(exc),
        )


def run_replay(
    dl_path: str,
    jobs: dict,
    *,
    purge_on_success: bool = True,
) -> ReplayReport:
    """Replay all entries in the dead-letter queue that have a matching job config."""
    report = ReplayReport()
    entries = list_entries(dl_path)
    for entry in entries:
        cfg = jobs.get(entry.job_name)
        if cfg is None:
            continue
        result = replay_job(entry, cfg)
        report.results.append(result)
        if result.success and purge_on_success:
            remove_entry(dl_path, entry.id)
    return report
