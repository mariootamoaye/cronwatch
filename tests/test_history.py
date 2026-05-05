"""Tests for cronwatch.history."""

import json
from pathlib import Path

import pytest

from cronwatch.history import (
    HistoryEntry,
    MAX_ENTRIES_PER_JOB,
    get_entries,
    last_entry,
    record,
)


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _make_entry(job_name: str = "backup", success: bool = True, exit_code: int = 0) -> HistoryEntry:
    return HistoryEntry(
        job_name=job_name,
        started_at="2024-01-15T10:00:00",
        duration_seconds=1.5,
        exit_code=exit_code,
        timed_out=False,
        success=success,
    )


def test_record_creates_file(history_file: Path) -> None:
    entry = _make_entry()
    record(entry, path=history_file)
    assert history_file.exists()


def test_record_and_retrieve(history_file: Path) -> None:
    entry = _make_entry(job_name="sync")
    record(entry, path=history_file)
    entries = get_entries("sync", path=history_file)
    assert len(entries) == 1
    assert entries[0].job_name == "sync"
    assert entries[0].success is True


def test_multiple_records_accumulate(history_file: Path) -> None:
    for i in range(5):
        record(_make_entry(job_name="cleanup"), path=history_file)
    entries = get_entries("cleanup", path=history_file)
    assert len(entries) == 5


def test_entries_pruned_at_max(history_file: Path) -> None:
    for _ in range(MAX_ENTRIES_PER_JOB + 10):
        record(_make_entry(job_name="prune_me"), path=history_file)
    entries = get_entries("prune_me", path=history_file)
    assert len(entries) == MAX_ENTRIES_PER_JOB


def test_last_entry_returns_most_recent(history_file: Path) -> None:
    record(_make_entry(job_name="report", success=True), path=history_file)
    record(_make_entry(job_name="report", success=False, exit_code=1), path=history_file)
    latest = last_entry("report", path=history_file)
    assert latest is not None
    assert latest.success is False
    assert latest.exit_code == 1


def test_last_entry_none_for_unknown_job(history_file: Path) -> None:
    assert last_entry("no_such_job", path=history_file) is None


def test_get_entries_empty_for_unknown_job(history_file: Path) -> None:
    assert get_entries("ghost", path=history_file) == []


def test_different_jobs_isolated(history_file: Path) -> None:
    record(_make_entry(job_name="alpha"), path=history_file)
    record(_make_entry(job_name="beta"), path=history_file)
    record(_make_entry(job_name="beta"), path=history_file)
    assert len(get_entries("alpha", path=history_file)) == 1
    assert len(get_entries("beta", path=history_file)) == 2


def test_corrupt_history_file_returns_empty(history_file: Path) -> None:
    history_file.write_text("not valid json")
    assert get_entries("any_job", path=history_file) == []
