"""Text rendering helpers for checkpoint data."""
from __future__ import annotations

from datetime import timezone
from typing import List, Optional

from cronwatch.checkpoint import CheckpointEntry

_COL_TS = 26
_COL_JOB = 20
_COL_NAME = 20


def _fmt_ts(entry: CheckpointEntry) -> str:
    dt = entry.dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def render_checkpoint_table(entries: List[CheckpointEntry]) -> str:
    """Return a fixed-width text table of checkpoint entries."""
    if not entries:
        return "No checkpoints to display."

    header = (
        f"{'TIMESTAMP':<{_COL_TS}}  "
        f"{'JOB':<{_COL_JOB}}  "
        f"{'CHECKPOINT':<{_COL_NAME}}  NOTE"
    )
    sep = "-" * (len(header) + 10)
    rows = [header, sep]
    for e in entries:
        note = e.note or ""
        row = (
            f"{_fmt_ts(e):<{_COL_TS}}  "
            f"{e.job:<{_COL_JOB}}  "
            f"{e.name:<{_COL_NAME}}  {note}"
        )
        rows.append(row)
    return "\n".join(rows)


def render_last_checkpoint(entry: Optional[CheckpointEntry]) -> str:
    """Single-line summary of the most recent checkpoint, or a fallback message."""
    if entry is None:
        return "No checkpoint recorded."
    note_part = f" ({entry.note})" if entry.note else ""
    return f"{_fmt_ts(entry)}  {entry.name}{note_part}"
