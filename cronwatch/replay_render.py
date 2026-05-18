"""Text rendering helpers for replay reports."""
from __future__ import annotations

from cronwatch.replay import ReplayReport, ReplayResult

_COL_NAME = 24
_COL_TS = 26
_COL_STATUS = 8
_COL_EXIT = 6


def _header() -> str:
    return (
        f"{'JOB':<{_COL_NAME}}  "
        f"{'ORIGINAL TIMESTAMP':<{_COL_TS}}  "
        f"{'STATUS':<{_COL_STATUS}}  "
        f"{'EXIT':>{_COL_EXIT}}"
    )


def _row(result: ReplayResult) -> str:
    status = "ok" if result.success else "FAILED"
    return (
        f"{result.job_name:<{_COL_NAME}}  "
        f"{result.original_ts:<{_COL_TS}}  "
        f"{status:<{_COL_STATUS}}  "
        f"{result.exit_code:>{_COL_EXIT}}"
    )


def render_replay_table(report: ReplayReport) -> str:
    """Return a formatted table of replay results."""
    if not report.results:
        return "No entries replayed."

    sep = "-" * (_COL_NAME + _COL_TS + _COL_STATUS + _COL_EXIT + 6)
    lines = [_header(), sep]
    for result in report.results:
        lines.append(_row(result))
        if result.error:
            lines.append(f"  {'':>{_COL_NAME}}  error: {result.error}")
    lines.append(sep)
    lines.append(
        f"Total: {report.total}  Succeeded: {report.succeeded}  Failed: {report.failed}"
    )
    return "\n".join(lines)
