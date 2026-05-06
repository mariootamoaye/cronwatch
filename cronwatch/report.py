"""Generate human-readable run reports from a RunSummary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from cronwatch.summary import RunSummary, SummaryLine


@dataclass
class ReportLine:
    job_name: str
    status: str
    duration_s: float
    exit_code: int | None
    note: str

    def as_text(self) -> str:
        parts = [
            f"{self.job_name:<30}",
            f"{self.status:<10}",
            f"{self.duration_s:>8.2f}s",
        ]
        if self.exit_code is not None:
            parts.append(f"exit={self.exit_code}")
        if self.note:
            parts.append(f"({self.note})")
        return "  ".join(parts)


@dataclass
class Report:
    lines: List[ReportLine]
    total: int
    ok_count: int
    failed_count: int

    @property
    def all_ok(self) -> bool:
        return self.failed_count == 0

    def as_text(self) -> str:
        header = f"{'JOB':<30}  {'STATUS':<10}  {'DURATION':>9}  DETAILS"
        separator = "-" * 70
        body = "\n".join(line.as_text() for line in self.lines)
        footer = (
            f"\nTotal: {self.total}  OK: {self.ok_count}  Failed: {self.failed_count}"
        )
        return "\n".join([header, separator, body, footer])


def _note_for(summary_line: SummaryLine) -> str:
    if summary_line.timed_out:
        return "timed out"
    if summary_line.exceeded_max_duration:
        return "exceeded max duration"
    if summary_line.status == "FAILED":
        return "non-zero exit"
    return ""


def build_report(summary: RunSummary) -> Report:
    lines: List[ReportLine] = []
    for sl in summary.lines:
        lines.append(
            ReportLine(
                job_name=sl.job_name,
                status=sl.status,
                duration_s=sl.duration_s,
                exit_code=sl.exit_code,
                note=_note_for(sl),
            )
        )
    ok_count = sum(1 for sl in summary.lines if sl.status == "OK")
    failed_count = len(summary.lines) - ok_count
    return Report(
        lines=lines,
        total=len(summary.lines),
        ok_count=ok_count,
        failed_count=failed_count,
    )
