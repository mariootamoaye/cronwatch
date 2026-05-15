"""Tests for cronwatch.checkpoint."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.checkpoint import (
    CheckpointEntry,
    record_checkpoint,
    list_checkpoints,
    last_checkpoint,
    clear_checkpoints,
)


@pytest.fixture()
def cp_file(tmp_path: Path) -> Path:
    return tmp_path / "checkpoints.json"


def test_record_creates_file(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="backup", name="start")
    assert cp_file.exists()


def test_record_returns_entry(cp_file: Path) -> None:
    entry = record_checkpoint(cp_file, job="backup", name="compress", note="gz")
    assert entry.job == "backup"
    assert entry.name == "compress"
    assert entry.note == "gz"
    assert entry.timestamp  # non-empty ISO string


def test_multiple_records_accumulate(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="backup", name="start")
    record_checkpoint(cp_file, job="backup", name="upload")
    record_checkpoint(cp_file, job="report", name="generate")
    entries = list_checkpoints(cp_file)
    assert len(entries) == 3


def test_list_filter_by_job(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="backup", name="start")
    record_checkpoint(cp_file, job="report", name="generate")
    entries = list_checkpoints(cp_file, job="backup")
    assert len(entries) == 1
    assert entries[0].job == "backup"


def test_list_empty_when_no_file(cp_file: Path) -> None:
    assert list_checkpoints(cp_file) == []


def test_last_checkpoint_returns_most_recent(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="backup", name="start")
    record_checkpoint(cp_file, job="backup", name="done")
    entry = last_checkpoint(cp_file, job="backup")
    assert entry is not None
    assert entry.name == "done"


def test_last_checkpoint_returns_none_for_unknown_job(cp_file: Path) -> None:
    assert last_checkpoint(cp_file, job="ghost") is None


def test_clear_removes_only_target_job(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="backup", name="start")
    record_checkpoint(cp_file, job="report", name="generate")
    removed = clear_checkpoints(cp_file, job="backup")
    assert removed == 1
    remaining = list_checkpoints(cp_file)
    assert len(remaining) == 1
    assert remaining[0].job == "report"


def test_clear_returns_zero_when_no_match(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="backup", name="start")
    removed = clear_checkpoints(cp_file, job="ghost")
    assert removed == 0


def test_round_trip_serialisation(cp_file: Path) -> None:
    record_checkpoint(cp_file, job="etl", name="extract", note="rows=500")
    raw = json.loads(cp_file.read_text())
    entry = CheckpointEntry.from_dict(raw[0])
    assert entry.job == "etl"
    assert entry.name == "extract"
    assert entry.note == "rows=500"
