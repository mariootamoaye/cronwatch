"""Tests for cronwatch.heartbeat."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.heartbeat import (
    HeartbeatReport,
    HeartbeatResult,
    build_heartbeat_report,
    check_heartbeat,
)


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _write_entry(path: str, job_name: str, started_at: datetime) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    row = {
        "job_name": job_name,
        "started_at": started_at.isoformat(),
        "duration_seconds": 1.0,
        "exit_code": 0,
        "timed_out": False,
        "note": "",
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def test_heartbeat_ok_when_run_recently(tmp_path):
    history = str(tmp_path / "backup.json")
    last_run = NOW - timedelta(hours=1)
    _write_entry(history, "backup", last_run)

    result = check_heartbeat("backup", history, expected_interval_hours=6.0, now=NOW)

    assert not result.is_late
    assert result.hours_overdue == 0.0
    assert result.last_run == last_run


def test_heartbeat_late_when_overdue(tmp_path):
    history = str(tmp_path / "backup.json")
    last_run = NOW - timedelta(hours=10)
    _write_entry(history, "backup", last_run)

    result = check_heartbeat("backup", history, expected_interval_hours=6.0, now=NOW)

    assert result.is_late
    assert result.hours_overdue == pytest.approx(4.0, abs=0.01)


def test_heartbeat_late_when_no_history(tmp_path):
    history = str(tmp_path / "missing.json")

    result = check_heartbeat("sync", history, expected_interval_hours=3.0, now=NOW)

    assert result.is_late
    assert result.last_run is None
    assert result.hours_overdue == 3.0


def test_heartbeat_report_all_ok(tmp_path):
    for job in ("a", "b"):
        path = str(tmp_path / f"{job}.json")
        _write_entry(path, job, NOW - timedelta(hours=1))

    report = build_heartbeat_report(
        {"a": 6.0, "b": 6.0}, history_dir=str(tmp_path), now=NOW
    )

    assert report.all_ok
    assert report.late_jobs == []
    assert len(report.results) == 2


def test_heartbeat_report_with_late_job(tmp_path):
    path_a = str(tmp_path / "a.json")
    _write_entry(path_a, "a", NOW - timedelta(hours=1))
    # job "b" has no history file → always late

    report = build_heartbeat_report(
        {"a": 6.0, "b": 2.0}, history_dir=str(tmp_path), now=NOW
    )

    assert not report.all_ok
    late_names = [r.job_name for r in report.late_jobs]
    assert "b" in late_names
    assert "a" not in late_names
