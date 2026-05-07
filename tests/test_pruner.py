"""Tests for cronwatch.pruner."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.config import RetentionConfig
from cronwatch.pruner import PruneReport, PrunerResult, prune_job, run_pruner


def _ts(days_ago: int = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _write_entries(path: Path, entries: list[dict]) -> None:
    path.write_text(json.dumps(entries))


@pytest.fixture()
def history_dir(tmp_path: Path) -> Path:
    d = tmp_path / "history"
    d.mkdir()
    return d


def test_run_pruner_empty_dir(history_dir: Path) -> None:
    cfg = RetentionConfig(max_age_days=30, max_entries=100)
    result = run_pruner(history_dir, cfg)
    assert isinstance(result, PrunerResult)
    assert result.total_removed == 0
    assert result.jobs_pruned == 0


def test_run_pruner_nonexistent_dir(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir"
    cfg = RetentionConfig(max_age_days=7)
    result = run_pruner(missing, cfg)
    assert result.total_removed == 0


def test_run_pruner_removes_old_entries(history_dir: Path) -> None:
    job_file = history_dir / "backup.json"
    entries = [
        {"timestamp": _ts(60), "exit_code": 0},
        {"timestamp": _ts(1), "exit_code": 0},
    ]
    _write_entries(job_file, entries)

    cfg = RetentionConfig(max_age_days=30)
    result = run_pruner(history_dir, cfg)

    assert result.total_removed == 1
    assert result.jobs_pruned == 1


def test_run_pruner_multiple_jobs(history_dir: Path) -> None:
    for name in ("job_a", "job_b"):
        f = history_dir / f"{name}.json"
        _write_entries(f, [{"timestamp": _ts(90), "exit_code": 1}])

    cfg = RetentionConfig(max_age_days=30)
    result = run_pruner(history_dir, cfg)

    assert result.jobs_pruned == 2
    assert result.total_removed == 2
    assert len(result.reports) == 2


def test_prune_job_no_rules_applied(history_dir: Path) -> None:
    job_file = history_dir / "noop.json"
    _write_entries(job_file, [{"timestamp": _ts(200), "exit_code": 0}])

    cfg = RetentionConfig()  # no limits set
    report = prune_job(job_file, cfg)

    assert report.age_result is None
    assert report.count_result is None
    assert report.total_removed == 0


def test_prune_report_total_removed_sums_both() -> None:
    from cronwatch.retention import RetentionResult

    report = PruneReport(
        job_name="test",
        age_result=RetentionResult(removed=3, remaining=5),
        count_result=RetentionResult(removed=2, remaining=3),
    )
    assert report.total_removed == 5
