"""Render annotation lists as formatted text tables."""
from __future__ import annotations

from typing import List

from cronwatch.annotation import Annotation

_JOB_W = 20
_AUTHOR_W = 12
_TS_W = 26
_RID_W = 12


def _truncate(s: str, width: int) -> str:
    return s[:width] if len(s) > width else s


def _header() -> str:
    cols = [
        f"{'TIMESTAMP':<{_TS_W}}",
        f"{'JOB':<{_JOB_W}}",
        f"{'RUN-ID':<{_RID_W}}",
        f"{'AUTHOR':<{_AUTHOR_W}}",
        "NOTE",
    ]
    line = "  ".join(cols)
    return line + "\n" + "-" * len(line)


def _row(a: Annotation) -> str:
    rid = a.run_id or "-"
    return "  ".join([
        f"{_truncate(a.created_at, _TS_W):<{_TS_W}}",
        f"{_truncate(a.job_name, _JOB_W):<{_JOB_W}}",
        f"{_truncate(rid, _RID_W):<{_RID_W}}",
        f"{_truncate(a.author, _AUTHOR_W):<{_AUTHOR_W}}",
        a.note,
    ])


def render_annotation_table(annotations: List[Annotation]) -> str:
    if not annotations:
        return "No annotations."
    lines = [_header()]
    for a in annotations:
        lines.append(_row(a))
    return "\n".join(lines)
