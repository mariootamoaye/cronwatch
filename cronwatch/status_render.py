"""Render a StatusBoard as plain text or a compact summary line."""

from __future__ import annotations

from cronwatch.status import JobStatus, StatusBoard

_COL_NAME = 28
_COL_LAST_RUN = 22
_COL_CODE = 6
_COL_DUR = 10
_COL_STREAK = 10


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m{secs:02d}s"


def _fmt_last_run(status: JobStatus) -> str:
    if status.last_run is None:
        return "never"
    return status.last_run.strftime("%Y-%m-%d %H:%M:%S")


def _fmt_code(status: JobStatus) -> str:
    if status.last_exit_code is None:
        return "-"
    return str(status.last_exit_code)


def _row(status: JobStatus) -> str:
    state = "OK" if status.ok else "FAIL"
    if status.never_run:
        state = "PENDING"
    streak = str(status.consecutive_failures) if status.consecutive_failures else "-"
    return (
        f"{status.job_name:<{_COL_NAME}}"
        f"{_fmt_last_run(status):<{_COL_LAST_RUN}}"
        f"{_fmt_code(status):<{_COL_CODE}}"
        f"{_fmt_duration(status.last_duration):<{_COL_DUR}}"
        f"{streak:<{_COL_STREAK}}"
        f"{state}"
    )


def render_status_board(board: StatusBoard) -> str:
    header = (
        f"{'JOB':<{_COL_NAME}}"
        f"{'LAST RUN':<{_COL_LAST_RUN}}"
        f"{'CODE':<{_COL_CODE}}"
        f"{'DURATION':<{_COL_DUR}}"
        f"{'FAILURES':<{_COL_STREAK}}"
        f"STATUS"
    )
    separator = "-" * len(header)
    rows = [header, separator] + [_row(j) for j in board.jobs]
    overall = "\nOverall: OK" if board.all_ok else f"\nOverall: {len(board.failing)} job(s) failing"
    rows.append(overall)
    return "\n".join(rows)
