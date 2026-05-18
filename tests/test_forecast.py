"""Tests for cronwatch.forecast."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.forecast import forecast_job, ForecastResult


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _entry(job: str, started_at: datetime, exit_code: int = 0) -> dict:
    return {
        "job_name": job,
        "started_at": started_at.isoformat(),
        "finished_at": (started_at + timedelta(seconds=5)).isoformat(),
        "exit_code": exit_code,
        "stdout": "",
        "stderr": "",
        "duration_seconds": 5.0,
    }


def _write(path: Path, entries: list) -> None:
    path.write_text(json.dumps(entries))


def _now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_forecast_no_history(history_file: Path) -> None:
    result = forecast_job("backup", history_file)
    assert result.confidence == "none"
    assert result.next_expected is None
    assert result.last_run is None


def test_forecast_insufficient_samples(history_file: Path) -> None:
    base = _now()
    entries = [_entry("backup", base + timedelta(hours=i)) for i in range(2)]
    _write(history_file, entries)
    result = forecast_job("backup", history_file)
    assert result.confidence == "low"
    assert result.next_expected is None
    assert result.last_run is not None


def test_forecast_enough_samples(history_file: Path) -> None:
    base = _now()
    entries = [_entry("backup", base + timedelta(hours=i)) for i in range(5)]
    _write(history_file, entries)
    result = forecast_job("backup", history_file)
    assert result.confidence == "low"  # < 10 samples
    assert result.next_expected is not None
    expected_interval = 3600.0
    assert abs(result.avg_interval_seconds - expected_interval) < 1


def test_forecast_high_confidence(history_file: Path) -> None:
    base = _now()
    entries = [_entry("backup", base + timedelta(hours=i)) for i in range(12)]
    _write(history_file, entries)
    result = forecast_job("backup", history_file)
    assert result.confidence == "high"


def test_forecast_next_expected_value(history_file: Path) -> None:
    base = _now()
    # 4 runs each exactly 1 hour apart → avg = 3600 s
    entries = [_entry("nightly", base + timedelta(hours=i)) for i in range(4)]
    _write(history_file, entries)
    result = forecast_job("nightly", history_file)
    last = max(e["started_at"] for e in entries)
    from datetime import datetime
    last_dt = datetime.fromisoformat(last)
    expected_next = last_dt + timedelta(seconds=3600)
    assert result.next_expected == expected_next


def test_forecast_ignores_other_jobs(history_file: Path) -> None:
    base = _now()
    entries = (
        [_entry("backup", base + timedelta(hours=i)) for i in range(5)]
        + [_entry("other", base + timedelta(minutes=i)) for i in range(5)]
    )
    _write(history_file, entries)
    result = forecast_job("backup", history_file)
    assert abs(result.avg_interval_seconds - 3600.0) < 1
