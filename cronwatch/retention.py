"""History retention policy: prune old entries from the history file."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List

from cronwatch.history import HistoryEntry, _load_raw, _save_raw


@dataclass
class RetentionResult:
    kept: int
    pruned: int

    @property
    def total(self) -> int:
        return self.kept + self.pruned


def _cutoff_date(days: int) -> datetime.datetime:
    return datetime.datetime.utcnow() - datetime.timedelta(days=days)


def prune_by_age(history_path: str, max_age_days: int) -> RetentionResult:
    """Remove entries older than *max_age_days* from the history file."""
    raw: List[dict] = _load_raw(history_path)
    cutoff = _cutoff_date(max_age_days)
    kept, pruned = [], []
    for entry in raw:
        ts = datetime.datetime.fromisoformat(entry["timestamp"])
        if ts >= cutoff:
            kept.append(entry)
        else:
            pruned.append(entry)
    _save_raw(history_path, kept)
    return RetentionResult(kept=len(kept), pruned=len(pruned))


def prune_by_count(history_path: str, max_entries: int) -> RetentionResult:
    """Keep only the *max_entries* most-recent entries."""
    raw: List[dict] = _load_raw(history_path)
    if len(raw) <= max_entries:
        return RetentionResult(kept=len(raw), pruned=0)
    kept = raw[-max_entries:]
    pruned_count = len(raw) - len(kept)
    _save_raw(history_path, kept)
    return RetentionResult(kept=len(kept), pruned=pruned_count)
