"""Trend analysis: detect improving or degrading job success rates over time."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from cronwatch.history import HistoryEntry, load_history


@dataclass
class TrendWindow:
    label: str
    total: int
    failures: int

    @property
    def success_rate(self) -> Optional[float]:
        if self.total == 0:
            return None
        return (self.total - self.failures) / self.total


@dataclass
class TrendResult:
    job: str
    recent: TrendWindow
    previous: TrendWindow

    @property
    def delta(self) -> Optional[float]:
        """Change in success rate (recent - previous). Positive = improving."""
        if self.recent.success_rate is None or self.previous.success_rate is None:
            return None
        return self.recent.success_rate - self.previous.success_rate

    @property
    def is_degrading(self) -> bool:
        d = self.delta
        return d is not None and d < -0.05

    @property
    def is_improving(self) -> bool:
        d = self.delta
        return d is not None and d > 0.05

    def __str__(self) -> str:
        r = self.recent.success_rate
        p = self.previous.success_rate
        r_str = f"{r:.0%}" if r is not None else "n/a"
        p_str = f"{p:.0%}" if p is not None else "n/a"
        direction = "degrading" if self.is_degrading else ("improving" if self.is_improving else "stable")
        return f"{self.job}: {p_str} -> {r_str} ({direction})"


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _count_failures(entries: List[HistoryEntry]) -> int:
    return sum(1 for e in entries if not e.success)


def analyze_trend(
    job: str,
    history_path: Path,
    window_days: int = 7,
) -> TrendResult:
    """Compare success rate in the last *window_days* vs the prior equal window."""
    all_entries = [e for e in load_history(history_path) if e.job == job]
    now = _now()
    cutoff_recent = now - timedelta(days=window_days)
    cutoff_previous = now - timedelta(days=window_days * 2)

    recent_entries = [e for e in all_entries if e.timestamp >= cutoff_recent]
    previous_entries = [
        e for e in all_entries if cutoff_previous <= e.timestamp < cutoff_recent
    ]

    recent = TrendWindow(
        label="recent",
        total=len(recent_entries),
        failures=_count_failures(recent_entries),
    )
    previous = TrendWindow(
        label="previous",
        total=len(previous_entries),
        failures=_count_failures(previous_entries),
    )
    return TrendResult(job=job, recent=recent, previous=previous)
