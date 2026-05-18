"""Tests for cronwatch.trend."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.trend import TrendResult, TrendWindow, analyze_trend


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _ts(days_ago: float) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _entry(job: str, success: bool, days_ago: float) -> dict:
    return {
        "job": job,
        "timestamp": _ts(days_ago),
        "success": success,
        "exit_code": 0 if success else 1,
        "duration": 1.0,
        "stdout": "",
        "stderr": "",
    }


def _write(path: Path, entries: list) -> None:
    path.write_text(json.dumps(entries))


def test_trend_all_ok(history_file: Path) -> None:
    entries = [_entry("backup", True, d) for d in range(1, 15)]
    _write(history_file, entries)
    result = analyze_trend("backup", history_file, window_days=7)
    assert result.recent.success_rate == 1.0
    assert result.previous.success_rate == 1.0
    assert not result.is_degrading
    assert not result.is_improving


def test_trend_degrading(history_file: Path) -> None:
    # previous window: all ok; recent window: all failing
    recent = [_entry("backup", False, d) for d in range(1, 8)]
    previous = [_entry("backup", True, d) for d in range(8, 15)]
    _write(history_file, recent + previous)
    result = analyze_trend("backup", history_file, window_days=7)
    assert result.recent.success_rate == 0.0
    assert result.previous.success_rate == 1.0
    assert result.is_degrading
    assert not result.is_improving


def test_trend_improving(history_file: Path) -> None:
    recent = [_entry("backup", True, d) for d in range(1, 8)]
    previous = [_entry("backup", False, d) for d in range(8, 15)]
    _write(history_file, recent + previous)
    result = analyze_trend("backup", history_file, window_days=7)
    assert result.is_improving
    assert not result.is_degrading


def test_trend_no_history(history_file: Path) -> None:
    _write(history_file, [])
    result = analyze_trend("backup", history_file, window_days=7)
    assert result.recent.total == 0
    assert result.previous.total == 0
    assert result.delta is None
    assert not result.is_degrading


def test_trend_str_stable(history_file: Path) -> None:
    entries = [_entry("sync", True, d) for d in range(1, 15)]
    _write(history_file, entries)
    result = analyze_trend("sync", history_file, window_days=7)
    assert "stable" in str(result)
    assert "sync" in str(result)


def test_trend_str_degrading(history_file: Path) -> None:
    recent = [_entry("sync", False, d) for d in range(1, 8)]
    previous = [_entry("sync", True, d) for d in range(8, 15)]
    _write(history_file, recent + previous)
    result = analyze_trend("sync", history_file, window_days=7)
    assert "degrading" in str(result)


def test_trend_window_label() -> None:
    w = TrendWindow(label="recent", total=10, failures=2)
    assert w.label == "recent"
    assert w.success_rate == pytest.approx(0.8)


def test_trend_window_empty_success_rate() -> None:
    w = TrendWindow(label="recent", total=0, failures=0)
    assert w.success_rate is None
