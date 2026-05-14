"""Tests for cronwatch.dependency."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.dependency import (
    DependencyResult,
    DependencyReport,
    check_dependencies,
    check_all_dependencies,
)


@pytest.fixture()
def history_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _write_entry(history_dir: str, job: str, exit_code: int) -> None:
    path = os.path.join(history_dir, f"{job}.jsonl")
    entry = {
        "job": job,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "duration": 1.0,
        "exit_code": exit_code,
        "stdout": "",
        "stderr": "",
    }
    with open(path, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def test_dependency_result_not_blocked():
    r = DependencyResult(job_name="child", blocked_by=[])
    assert not r.is_blocked
    assert "satisfied" in str(r)


def test_dependency_result_blocked():
    r = DependencyResult(job_name="child", blocked_by=["parent"])
    assert r.is_blocked
    assert "parent" in str(r)


def test_check_dependencies_ok(history_dir):
    _write_entry(history_dir, "parent", 0)
    result = check_dependencies("child", ["parent"], history_dir)
    assert not result.is_blocked


def test_check_dependencies_blocked_on_failure(history_dir):
    _write_entry(history_dir, "parent", 1)
    result = check_dependencies("child", ["parent"], history_dir)
    assert result.is_blocked
    assert "parent" in result.blocked_by


def test_check_dependencies_blocked_when_no_history(history_dir):
    result = check_dependencies("child", ["never_run"], history_dir)
    assert result.is_blocked
    assert "never_run" in result.blocked_by


def test_check_dependencies_multiple_deps(history_dir):
    _write_entry(history_dir, "dep_ok", 0)
    _write_entry(history_dir, "dep_fail", 1)
    result = check_dependencies("child", ["dep_ok", "dep_fail"], history_dir)
    assert result.is_blocked
    assert "dep_fail" in result.blocked_by
    assert "dep_ok" not in result.blocked_by


def test_check_all_dependencies_report(history_dir):
    _write_entry(history_dir, "a", 0)
    _write_entry(history_dir, "b", 1)
    jobs = {"child1": ["a"], "child2": ["b"]}
    report = check_all_dependencies(jobs, history_dir)
    assert not report.all_clear
    assert "child2" in report.blocked_jobs()
    assert "child1" not in report.blocked_jobs()


def test_check_all_dependencies_all_clear(history_dir):
    _write_entry(history_dir, "a", 0)
    jobs = {"child": ["a"]}
    report = check_all_dependencies(jobs, history_dir)
    assert report.all_clear
    assert report.blocked_jobs() == []
