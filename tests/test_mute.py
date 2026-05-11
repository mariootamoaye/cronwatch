"""Tests for cronwatch.mute."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.mute import (
    MuteEntry,
    is_muted,
    list_mutes,
    mute_job,
    unmute_job,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_FUTURE = _NOW + timedelta(hours=2)
_PAST = _NOW - timedelta(hours=1)


@pytest.fixture()
def mute_file(tmp_path: Path) -> Path:
    return tmp_path / "mutes.json"


def test_mute_entry_active():
    entry = MuteEntry(job_name="backup", muted_until=_FUTURE.isoformat())
    assert entry.is_active(_NOW) is True


def test_mute_entry_expired():
    entry = MuteEntry(job_name="backup", muted_until=_PAST.isoformat())
    assert entry.is_active(_NOW) is False


def test_mute_entry_expires_exactly_at_boundary():
    """An entry whose muted_until equals now should be considered expired."""
    entry = MuteEntry(job_name="backup", muted_until=_NOW.isoformat())
    assert entry.is_active(_NOW) is False


def test_mute_job_creates_file(mute_file: Path):
    mute_job("backup", _FUTURE, path=mute_file)
    assert mute_file.exists()
    data = json.loads(mute_file.read_text())
    assert len(data) == 1
    assert data[0]["job_name"] == "backup"


def test_mute_job_replaces_existing(mute_file: Path):
    mute_job("backup", _FUTURE, path=mute_file)
    new_until = _FUTURE + timedelta(hours=1)
    mute_job("backup", new_until, path=mute_file)
    data = json.loads(mute_file.read_text())
    assert len(data) == 1
    assert new_until.isoformat() in data[0]["muted_until"]


def test_mute_job_multiple_jobs(mute_file: Path):
    """Muting distinct jobs should create separate entries."""
    mute_job("job-a", _FUTURE, path=mute_file)
    mute_job("job-b", _FUTURE, path=mute_file)
    data = json.loads(mute_file.read_text())
    assert len(data) == 2
    names = {entry["job_name"] for entry in data}
    assert names == {"job-a", "job-b"}


def test_is_muted_returns_true_when_active(mute_file: Path):
    mute_job("backup", _FUTURE, path=mute_file)
    assert is_muted("backup", now=_NOW, path=mute_file) is True


def test_is_muted_returns_false_when_expired(mute_file: Path):
    mute_job("backup", _PAST, path=mute_file)
    assert is_muted("backup", now=_NOW, path=mute_file) is False


def test_is_muted_returns_false_when_absent(mute_file: Path):
    assert is_muted("backup", now=_NOW, path=mute_file) is False


def test_unmute_removes_entry(mute_file: Path):
    mute_job("backup", _FUTURE, path=mute_file)
    removed = unmute_job("backup", path=mute_file)
    assert removed is True
    assert is_muted("backup", now=_NOW, path=mute_file) is False


def test_unmute_returns_false_when_absent(mute_file: Path):
    assert unmute_job("nonexistent", path=mute_file) is False


def test_list_mutes_returns_only_active(mute_file: Path):
    mute_job("job-a", _FUTURE, path=mute_file)
    mute_job("job-b", _PAST, path=mute_file)
    active = list_mutes(path=mute_file, now=_NOW)
    names = [e.job_name for e in active]
    assert "job-a" in names
    assert "job-b" not in names


def test_list_mutes_empty_when_no_file(mute_file: Path):
    assert list_mutes(path=mute_file, now=_NOW) == []


def test_mute_reason_stored(mute_file: Path):
    mute_job("backup", _FUTURE, reason="maintenance", path=mute_file)
    entries = list_mutes(path=mute_file, now=_NOW)
    assert entries[0].reason == "maintenance"
