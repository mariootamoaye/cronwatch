"""Tests for cronwatch.overlap."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronwatch.overlap import (
    OverlapEntry,
    OverlapResult,
    acquire_lock,
    release_lock,
    _lock_path,
)


@pytest.fixture()
def lock_dir(tmp_path: Path) -> Path:
    return tmp_path / "locks"


# ---------------------------------------------------------------------------
# OverlapResult helpers
# ---------------------------------------------------------------------------

def test_overlap_result_ok_when_no_overlap(lock_dir):
    result = OverlapResult(job_name="backup", overlapping=False)
    assert result.ok is True


def test_overlap_result_not_ok_when_overlapping(lock_dir):
    entry = OverlapEntry(job_name="backup", pid=9999, started_at="2024-01-01T00:00:00+00:00")
    result = OverlapResult(job_name="backup", overlapping=True, existing_entry=entry)
    assert result.ok is False


def test_overlap_result_str_no_overlap():
    result = OverlapResult(job_name="sync", overlapping=False)
    assert "no overlap" in str(result)


def test_overlap_result_str_with_overlap():
    entry = OverlapEntry(job_name="sync", pid=1234, started_at="2024-06-01T10:00:00+00:00")
    result = OverlapResult(job_name="sync", overlapping=True, existing_entry=entry)
    text = str(result)
    assert "1234" in text
    assert "2024-06-01" in text


# ---------------------------------------------------------------------------
# acquire_lock / release_lock
# ---------------------------------------------------------------------------

def test_acquire_lock_creates_lock_file(lock_dir):
    result = acquire_lock("myjob", lock_dir)
    assert result.ok
    assert _lock_path(lock_dir, "myjob").exists()


def test_acquire_lock_records_current_pid(lock_dir):
    acquire_lock("myjob", lock_dir)
    data = json.loads(_lock_path(lock_dir, "myjob").read_text())
    assert data["pid"] == os.getpid()


def test_acquire_lock_detects_live_process(lock_dir):
    # First acquisition succeeds.
    acquire_lock("myjob", lock_dir)
    # Second acquisition should detect overlap (same PID is alive).
    result = acquire_lock("myjob", lock_dir)
    assert result.overlapping is True
    assert result.existing_entry is not None


def test_acquire_lock_clears_stale_lock(lock_dir):
    # Write a lock file with a PID that does not exist.
    lock_dir.mkdir(parents=True, exist_ok=True)
    stale = OverlapEntry(job_name="myjob", pid=999999, started_at="2024-01-01T00:00:00+00:00")
    _lock_path(lock_dir, "myjob").write_text(json.dumps(stale.to_dict()))

    result = acquire_lock("myjob", lock_dir)
    assert result.ok is True


def test_acquire_lock_handles_corrupt_lock_file(lock_dir):
    lock_dir.mkdir(parents=True, exist_ok=True)
    _lock_path(lock_dir, "myjob").write_text("not-json")
    result = acquire_lock("myjob", lock_dir)
    assert result.ok is True


def test_release_lock_removes_file(lock_dir):
    acquire_lock("myjob", lock_dir)
    removed = release_lock("myjob", lock_dir)
    assert removed is True
    assert not _lock_path(lock_dir, "myjob").exists()


def test_release_lock_returns_false_when_no_file(lock_dir):
    lock_dir.mkdir(parents=True, exist_ok=True)
    assert release_lock("ghost", lock_dir) is False


def test_job_name_with_slashes_uses_safe_filename(lock_dir):
    acquire_lock("a/b/c", lock_dir)
    assert _lock_path(lock_dir, "a/b/c").exists()
    assert "/" not in _lock_path(lock_dir, "a/b/c").name
