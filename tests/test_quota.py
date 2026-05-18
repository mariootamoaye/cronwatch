"""Tests for cronwatch.quota and cronwatch.quota_cli."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.quota import QuotaEntry, QuotaResult, check_quota, record_run


@pytest.fixture()
def quota_file(tmp_path: Path) -> Path:
    return tmp_path / "quota.json"


def _ts(delta_hours: float = 0.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=delta_hours)).isoformat()


def _write_entries(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries))


# ---------------------------------------------------------------------------
# QuotaEntry
# ---------------------------------------------------------------------------

def test_quota_entry_round_trip():
    entry = QuotaEntry(job_name="backup", ran_at=_ts())
    assert QuotaEntry.from_dict(entry.to_dict()) == entry


def test_quota_entry_dt_parses_iso():
    ts = "2024-06-01T12:00:00+00:00"
    entry = QuotaEntry(job_name="x", ran_at=ts)
    assert entry.dt().year == 2024


# ---------------------------------------------------------------------------
# record_run
# ---------------------------------------------------------------------------

def test_record_run_creates_file(quota_file: Path):
    record_run("backup", quota_file)
    assert quota_file.exists()


def test_record_run_appends_entries(quota_file: Path):
    record_run("backup", quota_file)
    record_run("backup", quota_file)
    data = json.loads(quota_file.read_text())
    assert len(data) == 2


def test_record_run_stores_job_name(quota_file: Path):
    record_run("sync", quota_file)
    data = json.loads(quota_file.read_text())
    assert data[0]["job_name"] == "sync"


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

def test_check_quota_no_history(quota_file: Path):
    result = check_quota("backup", limit=5, window_hours=24, quota_file=quota_file)
    assert result.count == 0
    assert not result.exceeded


def test_check_quota_within_limit(quota_file: Path):
    entries = [{"job_name": "backup", "ran_at": _ts(1)} for _ in range(3)]
    _write_entries(quota_file, entries)
    result = check_quota("backup", limit=5, window_hours=24, quota_file=quota_file)
    assert result.count == 3
    assert not result.exceeded


def test_check_quota_exceeded(quota_file: Path):
    entries = [{"job_name": "backup", "ran_at": _ts(0.5)} for _ in range(6)]
    _write_entries(quota_file, entries)
    result = check_quota("backup", limit=5, window_hours=24, quota_file=quota_file)
    assert result.exceeded


def test_check_quota_ignores_old_entries(quota_file: Path):
    old = [{"job_name": "backup", "ran_at": _ts(48)} for _ in range(10)]
    recent = [{"job_name": "backup", "ran_at": _ts(1)}]
    _write_entries(quota_file, old + recent)
    result = check_quota("backup", limit=5, window_hours=24, quota_file=quota_file)
    assert result.count == 1
    assert not result.exceeded


def test_check_quota_ignores_other_jobs(quota_file: Path):
    entries = [{"job_name": "other", "ran_at": _ts(1)} for _ in range(10)]
    _write_entries(quota_file, entries)
    result = check_quota("backup", limit=5, window_hours=24, quota_file=quota_file)
    assert result.count == 0


def test_quota_result_str_ok():
    r = QuotaResult(job_name="backup", limit=5, window_hours=24, count=2, exceeded=False)
    assert "ok" in str(r)
    assert "backup" in str(r)


def test_quota_result_str_exceeded():
    r = QuotaResult(job_name="backup", limit=5, window_hours=24, count=6, exceeded=True)
    assert "EXCEEDED" in str(r)
