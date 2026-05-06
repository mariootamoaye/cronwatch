"""Tests for cronwatch.retention."""
from __future__ import annotations

import datetime
import json
import pathlib

import pytest

from cronwatch.retention import prune_by_age, prune_by_count, RetentionResult


@pytest.fixture()
def history_file(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "history.json"


def _write_entries(path: pathlib.Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries))


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


def _old(days: int = 10) -> str:
    ts = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    return ts.isoformat()


def test_prune_by_age_removes_old_entries(history_file):
    entries = [
        {"job": "a", "timestamp": _old(20), "exit_code": 0},
        {"job": "b", "timestamp": _now(), "exit_code": 0},
    ]
    _write_entries(history_file, entries)
    result = prune_by_age(str(history_file), max_age_days=7)
    assert result.kept == 1
    assert result.pruned == 1


def test_prune_by_age_keeps_all_recent(history_file):
    entries = [{"job": "a", "timestamp": _now(), "exit_code": 0}]
    _write_entries(history_file, entries)
    result = prune_by_age(str(history_file), max_age_days=30)
    assert result.kept == 1
    assert result.pruned == 0


def test_prune_by_age_empty_file(history_file):
    _write_entries(history_file, [])
    result = prune_by_age(str(history_file), max_age_days=7)
    assert result == RetentionResult(kept=0, pruned=0)


def test_prune_by_count_keeps_most_recent(history_file):
    entries = [
        {"job": "a", "timestamp": _old(5), "exit_code": 0},
        {"job": "b", "timestamp": _old(3), "exit_code": 1},
        {"job": "c", "timestamp": _now(), "exit_code": 0},
    ]
    _write_entries(history_file, entries)
    result = prune_by_count(str(history_file), max_entries=2)
    assert result.kept == 2
    assert result.pruned == 1
    remaining = json.loads(history_file.read_text())
    assert remaining[0]["job"] == "b"
    assert remaining[1]["job"] == "c"


def test_prune_by_count_no_op_when_under_limit(history_file):
    entries = [{"job": "a", "timestamp": _now(), "exit_code": 0}]
    _write_entries(history_file, entries)
    result = prune_by_count(str(history_file), max_entries=10)
    assert result.kept == 1
    assert result.pruned == 0


def test_retention_result_total():
    r = RetentionResult(kept=3, pruned=2)
    assert r.total == 5
