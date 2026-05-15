"""Tests for cronwatch.threshold and cronwatch.threshold_cli."""
from __future__ import annotations

import json
import os
import pytest

from cronwatch.threshold import (
    ThresholdResult,
    ThresholdReport,
    check_threshold,
    _failure_rate,
    _avg_duration,
    _max_duration,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_history(path: str, entries: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(entries, fh)


def _entry(exit_code: int = 0, duration: float = 1.0) -> dict:
    return {
        "job_name": "test_job",
        "started_at": "2024-01-01T00:00:00",
        "finished_at": "2024-01-01T00:00:01",
        "exit_code": exit_code,
        "duration_seconds": duration,
        "stdout": "",
        "stderr": "",
    }


@pytest.fixture()
def history_file(tmp_path):
    return str(tmp_path / "history" / "test_job.json")


# ---------------------------------------------------------------------------
# Unit tests for metric helpers
# ---------------------------------------------------------------------------

def test_failure_rate_all_ok():
    from cronwatch.history import HistoryEntry
    entries = [HistoryEntry(**_entry(0)) for _ in range(4)]
    assert _failure_rate(entries) == 0.0


def test_failure_rate_half_failed():
    from cronwatch.history import HistoryEntry
    entries = [HistoryEntry(**_entry(0)), HistoryEntry(**_entry(1))]
    assert _failure_rate(entries) == pytest.approx(0.5)


def test_avg_duration_calculation():
    from cronwatch.history import HistoryEntry
    entries = [HistoryEntry(**_entry(duration=d)) for d in [2.0, 4.0, 6.0]]
    assert _avg_duration(entries) == pytest.approx(4.0)


def test_max_duration_calculation():
    from cronwatch.history import HistoryEntry
    entries = [HistoryEntry(**_entry(duration=d)) for d in [1.0, 9.0, 3.0]]
    assert _max_duration(entries) == pytest.approx(9.0)


# ---------------------------------------------------------------------------
# check_threshold integration
# ---------------------------------------------------------------------------

def test_check_threshold_not_breached(history_file):
    _write_history(history_file, [_entry(0, 1.0)] * 5)
    result = check_threshold("test_job", "failure_rate", 0.5, history_file)
    assert not result.breached
    assert result.metric == "failure_rate"


def test_check_threshold_breached(history_file):
    entries = [_entry(1, 1.0)] * 8 + [_entry(0, 1.0)] * 2  # 80% failure
    _write_history(history_file, entries)
    result = check_threshold("test_job", "failure_rate", 0.5, history_file)
    assert result.breached
    assert result.value == pytest.approx(0.8)


def test_check_threshold_window_limits_entries(history_file):
    # 10 old failures + 5 recent successes; window=5 should see 0% failure
    entries = [_entry(1)] * 10 + [_entry(0)] * 5
    _write_history(history_file, entries)
    result = check_threshold("test_job", "failure_rate", 0.1, history_file, window=5)
    assert not result.breached


def test_check_threshold_unknown_metric_raises(history_file):
    _write_history(history_file, [_entry()])
    with pytest.raises(ValueError, match="Unknown metric"):
        check_threshold("test_job", "nonexistent", 1.0, history_file)


# ---------------------------------------------------------------------------
# ThresholdReport
# ---------------------------------------------------------------------------

def test_report_all_ok():
    r = ThresholdReport(results=[
        ThresholdResult("j", "failure_rate", 0.1, 0.5, False),
    ])
    assert r.all_ok
    assert r.breached == []


def test_report_with_breach():
    ok = ThresholdResult("j", "failure_rate", 0.1, 0.5, False)
    bad = ThresholdResult("j", "avg_duration", 120.0, 60.0, True)
    r = ThresholdReport(results=[ok, bad])
    assert not r.all_ok
    assert len(r.breached) == 1
    assert bad in r.breached


def test_threshold_result_str_breached():
    r = ThresholdResult("myjob", "max_duration", 200.0, 100.0, True)
    assert "BREACHED" in str(r)
    assert "myjob" in str(r)
