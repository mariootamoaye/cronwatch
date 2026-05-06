"""Generate human-readable run summaries from scheduler results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from cronwatch.scheduler import SchedulerResult
from cronwatch.runner import JobResult


@dataclass
class SummaryLine:
    job_name: str
    status: str
    duration_s: float
    exit_code: int
    note: str


@dataclass
class RunSummary:
    generated_at: str
    total: int
    passed: int
    failed: int
    lines: List[SummaryLine]

    @property
    def all_ok(self) -> bool:
        return self.failed == 0


def _status_for(result: JobResult) -> tuple[str, str]:
    """Return (status_label, note) for a JobResult."""
    if result.timed_out:
        return "TIMEOUT", f"exceeded max duration"
    if result.returncode != 0:
        return "FAILED", f"exit code {result.returncode}"
    if result.duration_exceeded:
        return "SLOW", f"duration {result.duration_s:.1f}s exceeded threshold"
    return "OK", ""


def build_summary(scheduler_result: SchedulerResult) -> RunSummary:
    """Build a RunSummary from a SchedulerResult."""
    lines: List[SummaryLine] = []
    for job_name, job_result in scheduler_result.results.items():
        status, note = _status_for(job_result)
        lines.append(
            SummaryLine(
                job_name=job_name,
                status=status,
                duration_s=round(job_result.duration_s, 3),
                exit_code=job_result.returncode,
                note=note,
            )
        )

    passed = sum(1 for ln in lines if ln.status == "OK")
    failed = len(lines) - passed

    return RunSummary(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total=len(lines),
        passed=passed,
        failed=failed,
        lines=lines,
    )


def format_summary(summary: RunSummary) -> str:
    """Render a RunSummary as a plain-text table."""
    header = f"Cronwatch Run Summary  [{summary.generated_at}]"
    sep = "-" * 60
    rows = [header, sep, f"  Total: {summary.total}  Passed: {summary.passed}  Failed: {summary.failed}", sep]
    for ln in summary.lines:
        note_part = f"  # {ln.note}" if ln.note else ""
        rows.append(f"  [{ln.status:<7}] {ln.job_name:<30} {ln.duration_s:>7.3f}s{note_part}")
    rows.append(sep)
    return "\n".join(rows)
