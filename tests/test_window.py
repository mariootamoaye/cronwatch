"""Tests for cronwatch.window maintenance-window module."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.window import (
    WindowEntry,
    add_window,
    is_in_window,
    list_windows,
    purge_expired,
)

_NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
_BEFORE = (_NOW - timedelta(hours=1)).isoformat()
_AFTER = (_NOW + timedelta(hours=1)).isoformat()
_PAST = (_NOW - timedelta(hours=2)).isoformat()


@pytest.fixture()
def win_file(tmp_path: Path) -> Path:
    return tmp_path / "windows.json"


def test_window_entry_active():
    entry = WindowEntry(job="backup", start=_BEFORE, end=_AFTER)
    assert entry.is_active(_NOW) is True


def test_window_entry_not_active_before_start():
    future = (_NOW + timedelta(hours=1)).isoformat()
    far_future = (_NOW + timedelta(hours=2)).isoformat()
    entry = WindowEntry(job="backup", start=future, end=far_future)
    assert entry.is_active(_NOW) is False


def test_window_entry_not_active_after_end():
    entry = WindowEntry(job="backup", start=_PAST, end=_BEFORE)
    assert entry.is_active(_NOW) is False


def test_add_window_creates_file(win_file: Path):
    add_window("deploy", _BEFORE, _AFTER, path=win_file)
    assert win_file.exists()


def test_add_window_stores_fields(win_file: Path):
    add_window("deploy", _BEFORE, _AFTER, reason="planned", path=win_file)
    entries = list_windows(win_file)
    assert len(entries) == 1
    e = entries[0]
    assert e.job == "deploy"
    assert e.reason == "planned"


def test_add_multiple_windows(win_file: Path):
    add_window("job-a", _BEFORE, _AFTER, path=win_file)
    add_window("job-b", _BEFORE, _AFTER, path=win_file)
    assert len(list_windows(win_file)) == 2


def test_is_in_window_true(win_file: Path):
    add_window("nightly", _BEFORE, _AFTER, path=win_file)
    assert is_in_window("nightly", now=_NOW, path=win_file) is True


def test_is_in_window_false_wrong_job(win_file: Path):
    add_window("nightly", _BEFORE, _AFTER, path=win_file)
    assert is_in_window("other", now=_NOW, path=win_file) is False


def test_is_in_window_false_no_file(win_file: Path):
    assert is_in_window("any", now=_NOW, path=win_file) is False


def test_purge_expired_removes_old_windows(win_file: Path):
    add_window("old", _PAST, _BEFORE, path=win_file)   # expired
    add_window("live", _BEFORE, _AFTER, path=win_file)  # active
    removed = purge_expired(path=win_file, now=_NOW)
    assert removed == 1
    remaining = list_windows(win_file)
    assert len(remaining) == 1
    assert remaining[0].job == "live"


def test_purge_expired_empty_file(win_file: Path):
    removed = purge_expired(path=win_file, now=_NOW)
    assert removed == 0


def test_round_trip_serialisation(win_file: Path):
    add_window("svc", _BEFORE, _AFTER, reason="maint", path=win_file)
    raw = json.loads(win_file.read_text())
    restored = WindowEntry.from_dict(raw[0])
    assert restored.job == "svc"
    assert restored.reason == "maint"
