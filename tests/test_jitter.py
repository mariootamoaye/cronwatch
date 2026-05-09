"""Tests for cronwatch.jitter."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import pytest

from cronwatch.jitter import JitterEntry, JitterReport, check_jitter, _compute_jitter
from cronwatch.history import HistoryEntry


def _entry(job_name: str, started_at: datetime) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at=started_at,
        duration_seconds=1.0,
        exit_code=0,
        stdout="",
        stderr="",
    )


def _write(path: str, entries: list) -> None:
    with open(path, "w") as f:
        json.dump([e.to_dict() for e in entries], f)


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "history.json")


def test_jitter_entry_late():
    e = JitterEntry(
        job_name="backup",
        expected_interval_seconds=3600,
        actual_interval_seconds=3720,
        deviation_seconds=120,
        timestamp=datetime.utcnow(),
    )
    assert e.is_late
    assert not e.is_early


def test_jitter_entry_early():
    e = JitterEntry(
        job_name="backup",
        expected_interval_seconds=3600,
        actual_interval_seconds=3480,
        deviation_seconds=-120,
        timestamp=datetime.utcnow(),
    )
    assert e.is_early
    assert not e.is_late


def test_compute_jitter_two_runs():
    base = datetime(2024, 1, 1, 12, 0, 0)
    entries = [
        _entry("myjob", base),
        _entry("myjob", base + timedelta(seconds=3720)),
    ]
    result = _compute_jitter(entries, expected_interval_seconds=3600)
    assert len(result) == 1
    assert abs(result[0].deviation_seconds - 120) < 0.01


def test_compute_jitter_no_pairs():
    base = datetime(2024, 1, 1, 12, 0, 0)
    result = _compute_jitter([_entry("myjob", base)], expected_interval_seconds=3600)
    assert result == []


def test_report_all_ok_within_threshold():
    report = JitterReport(
        entries=[
            JitterEntry("j", 3600, 3610, 10, datetime.utcnow()),
        ],
        threshold_seconds=60,
    )
    assert report.all_ok
    assert report.violations == []


def test_report_violation_exceeds_threshold():
    report = JitterReport(
        entries=[
            JitterEntry("j", 3600, 3800, 200, datetime.utcnow()),
        ],
        threshold_seconds=60,
    )
    assert not report.all_ok
    assert len(report.violations) == 1


def test_check_jitter_from_history(history_file):
    base = datetime(2024, 6, 1, 8, 0, 0)
    entries = [
        _entry("sync", base),
        _entry("sync", base + timedelta(seconds=3600)),
        _entry("sync", base + timedelta(seconds=7300)),
        _entry("other", base + timedelta(seconds=100)),
    ]
    _write(history_file, entries)

    report = check_jitter(history_file, "sync", expected_interval_seconds=3600, threshold_seconds=60)
    assert len(report.entries) == 2
    assert all(e.job_name == "sync" for e in report.entries)
    # second interval: 7300 - 3600 = 3700, deviation = 100 > 60
    assert not report.all_ok


def test_check_jitter_respects_lookback(history_file):
    now = datetime.utcnow()
    entries = [
        _entry("job", now - timedelta(hours=5)),
        _entry("job", now - timedelta(hours=4)),
        _entry("job", now - timedelta(minutes=30)),
    ]
    _write(history_file, entries)

    report = check_jitter(
        history_file, "job",
        expected_interval_seconds=3600,
        lookback=timedelta(hours=2),
    )
    # Only the last entry falls within lookback=2h, so no pairs
    assert len(report.entries) == 0
