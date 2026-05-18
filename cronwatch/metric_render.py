"""Render metric summaries and sample lists as text tables."""
from __future__ import annotations

from typing import List, Optional

from cronwatch.metric import MetricSample, MetricSummary

_COL = (
    ("JOB", 24),
    ("SAMPLES", 9),
    ("MIN (s)", 9),
    ("AVG (s)", 9),
    ("P95 (s)", 9),
    ("MAX (s)", 9),
)


def _header() -> str:
    return "  ".join(name.ljust(w) for name, w in _COL)


def _summary_row(s: MetricSummary) -> str:
    return "  ".join([
        s.job_name[:24].ljust(24),
        str(s.sample_count).ljust(9),
        f"{s.min_duration:.2f}".ljust(9),
        f"{s.avg_duration:.2f}".ljust(9),
        f"{s.p95_duration:.2f}".ljust(9),
        f"{s.max_duration:.2f}".ljust(9),
    ])


def render_summary_table(summaries: List[MetricSummary]) -> str:
    if not summaries:
        return "No metric data available."
    lines = [_header(), "-" * 75]
    for s in summaries:
        lines.append(_summary_row(s))
    return "\n".join(lines)


def render_sample_table(samples: List[MetricSample]) -> str:
    if not samples:
        return "No samples found."
    header = "  ".join([
        "TIMESTAMP".ljust(26),
        "DURATION (s)".ljust(14),
        "EXIT CODE".ljust(10),
    ])
    sep = "-" * 54
    lines = [header, sep]
    for s in samples:
        lines.append("  ".join([
            s.timestamp[:26].ljust(26),
            f"{s.duration_seconds:.3f}".ljust(14),
            str(s.exit_code).ljust(10),
        ]))
    return "\n".join(lines)
