"""Render ForecastResult objects as human-readable text."""
from __future__ import annotations

from typing import List

from cronwatch.forecast import ForecastResult

_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _fmt_dt(dt) -> str:
    return dt.strftime(_DATE_FMT) if dt else "—"


def _fmt_interval(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    minutes = seconds / 60
    if minutes < 90:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    if hours < 36:
        return f"{hours:.1f}h"
    return f"{hours / 24:.1f}d"


def render_forecast_table(results: List[ForecastResult]) -> str:
    """Return a plain-text table of forecast results."""
    if not results:
        return "No forecast data available."

    header = f"{'JOB':<30} {'LAST RUN':<22} {'AVG INTERVAL':<14} {'NEXT EXPECTED':<22} CONFIDENCE"
    sep = "-" * len(header)
    rows = [header, sep]

    for r in results:
        rows.append(
            f"{r.job_name:<30} "
            f"{_fmt_dt(r.last_run):<22} "
            f"{_fmt_interval(r.avg_interval_seconds):<14} "
            f"{_fmt_dt(r.next_expected):<22} "
            f"{r.confidence}"
        )

    return "\n".join(rows)
