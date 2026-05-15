"""Tests for cronwatch.annotation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.annotation import (
    Annotation,
    add_annotation,
    delete_annotations,
    list_annotations,
)


@pytest.fixture()
def ann_file(tmp_path: Path) -> Path:
    return tmp_path / "annotations.json"


def test_add_annotation_creates_file(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "ran manually", "alice")
    assert ann_file.exists()


def test_add_annotation_stores_fields(ann_file: Path) -> None:
    entry = add_annotation(ann_file, "backup", "ran manually", "alice", run_id="abc123")
    assert entry.job_name == "backup"
    assert entry.note == "ran manually"
    assert entry.author == "alice"
    assert entry.run_id == "abc123"
    assert entry.created_at  # not empty


def test_multiple_annotations_accumulate(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "first note", "alice")
    add_annotation(ann_file, "backup", "second note", "bob")
    raw = json.loads(ann_file.read_text())
    assert len(raw) == 2


def test_list_all_annotations(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "note a", "alice")
    add_annotation(ann_file, "cleanup", "note b", "bob")
    results = list_annotations(ann_file)
    assert len(results) == 2


def test_list_filter_by_job(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "note a", "alice")
    add_annotation(ann_file, "cleanup", "note b", "bob")
    results = list_annotations(ann_file, job_name="backup")
    assert len(results) == 1
    assert results[0].job_name == "backup"


def test_list_filter_by_run_id(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "note a", "alice", run_id="run-1")
    add_annotation(ann_file, "backup", "note b", "bob", run_id="run-2")
    results = list_annotations(ann_file, run_id="run-1")
    assert len(results) == 1
    assert results[0].run_id == "run-1"


def test_list_empty_file_returns_empty(ann_file: Path) -> None:
    assert list_annotations(ann_file) == []


def test_delete_annotations_removes_by_job(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "note a", "alice")
    add_annotation(ann_file, "backup", "note b", "bob")
    add_annotation(ann_file, "cleanup", "note c", "carol")
    removed = delete_annotations(ann_file, "backup")
    assert removed == 2
    remaining = list_annotations(ann_file)
    assert len(remaining) == 1
    assert remaining[0].job_name == "cleanup"


def test_delete_nonexistent_job_returns_zero(ann_file: Path) -> None:
    add_annotation(ann_file, "backup", "note", "alice")
    removed = delete_annotations(ann_file, "does-not-exist")
    assert removed == 0


def test_round_trip_serialisation(ann_file: Path) -> None:
    add_annotation(ann_file, "job1", "hello", "dave", run_id="r99")
    raw = json.loads(ann_file.read_text())[0]
    restored = Annotation.from_dict(raw)
    assert restored.job_name == "job1"
    assert restored.note == "hello"
    assert restored.run_id == "r99"
