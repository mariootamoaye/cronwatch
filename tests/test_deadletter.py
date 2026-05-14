"""Tests for cronwatch.deadletter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.deadletter import (
    DeadLetterEntry,
    enqueue,
    list_entries,
    remove_entry,
    clear,
)


@pytest.fixture
def dl_file(tmp_path) -> Path:
    return tmp_path / "deadletter.json"


_PAYLOAD = {"subject": "Job failed", "body": "details"}


def test_enqueue_creates_file(dl_file):
    enqueue("backup", "email", _PAYLOAD, "SMTP timeout", path=dl_file)
    assert dl_file.exists()


def test_enqueue_stores_entry(dl_file):
    entry = enqueue("backup", "email", _PAYLOAD, "SMTP timeout", path=dl_file)
    entries = list_entries(path=dl_file)
    assert len(entries) == 1
    assert entries[0].job_name == "backup"
    assert entries[0].alert_type == "email"
    assert entries[0].error == "SMTP timeout"
    assert entries[0].attempts == 1
    assert entries[0].queued_at == entry.queued_at


def test_enqueue_multiple_entries(dl_file):
    enqueue("job_a", "email", _PAYLOAD, "err1", path=dl_file)
    enqueue("job_b", "webhook", _PAYLOAD, "err2", path=dl_file)
    entries = list_entries(path=dl_file)
    assert len(entries) == 2
    names = {e.job_name for e in entries}
    assert names == {"job_a", "job_b"}


def test_list_entries_empty_when_no_file(dl_file):
    entries = list_entries(path=dl_file)
    assert entries == []


def test_remove_entry_returns_true_when_found(dl_file):
    entry = enqueue("backup", "email", _PAYLOAD, "err", path=dl_file)
    removed = remove_entry("backup", entry.queued_at, path=dl_file)
    assert removed is True
    assert list_entries(path=dl_file) == []


def test_remove_entry_returns_false_when_not_found(dl_file):
    enqueue("backup", "email", _PAYLOAD, "err", path=dl_file)
    removed = remove_entry("backup", "1970-01-01T00:00:00+00:00", path=dl_file)
    assert removed is False
    assert len(list_entries(path=dl_file)) == 1


def test_remove_entry_leaves_others_intact(dl_file):
    e1 = enqueue("job_a", "email", _PAYLOAD, "err", path=dl_file)
    enqueue("job_b", "webhook", _PAYLOAD, "err", path=dl_file)
    remove_entry("job_a", e1.queued_at, path=dl_file)
    remaining = list_entries(path=dl_file)
    assert len(remaining) == 1
    assert remaining[0].job_name == "job_b"


def test_clear_removes_all_entries(dl_file):
    enqueue("job_a", "email", _PAYLOAD, "e1", path=dl_file)
    enqueue("job_b", "email", _PAYLOAD, "e2", path=dl_file)
    count = clear(path=dl_file)
    assert count == 2
    assert list_entries(path=dl_file) == []


def test_clear_returns_zero_when_empty(dl_file):
    assert clear(path=dl_file) == 0


def test_entry_round_trip_via_dict():
    original = DeadLetterEntry(
        job_name="nightly",
        alert_type="webhook",
        payload={"url": "https://hooks.example.com"},
        error="Connection refused",
        queued_at="2024-06-01T12:00:00+00:00",
        attempts=3,
    )
    restored = DeadLetterEntry.from_dict(original.to_dict())
    assert restored == original
