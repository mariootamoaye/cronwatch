"""Tests for cronwatch.escalation."""
import json
from pathlib import Path

import pytest

from cronwatch.escalation import check_escalation
from cronwatch.history import HistoryEntry, record


@pytest.fixture()
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _entry(job: str, exit_code: int, timed_out: bool = False, ts: str = "2024-01-01T00:00:00") -> HistoryEntry:
    return HistoryEntry(
        job_name=job,
        started_at=ts,
        duration_seconds=1.0,
        exit_code=exit_code,
        timed_out=timed_out,
    )


def test_no_history_does_not_escalate(history_file: Path) -> None:
    result = check_escalation("backup", history_file, threshold=3)
    assert result.consecutive_failures == 0
    assert not result.should_escalate
    assert result.ok


def test_single_failure_below_threshold(history_file: Path) -> None:
    record(history_file, _entry("backup", exit_code=1, ts="2024-01-01T01:00:00"))
    result = check_escalation("backup", history_file, threshold=3)
    assert result.consecutive_failures == 1
    assert not result.should_escalate


def test_consecutive_failures_reach_threshold(history_file: Path) -> None:
    for i in range(3):
        record(history_file, _entry("backup", exit_code=1, ts=f"2024-01-01T0{i}:00:00"))
    result = check_escalation("backup", history_file, threshold=3)
    assert result.consecutive_failures == 3
    assert result.should_escalate
    assert not result.ok


def test_success_resets_streak(history_file: Path) -> None:
    record(history_file, _entry("backup", exit_code=1, ts="2024-01-01T00:00:00"))
    record(history_file, _entry("backup", exit_code=0, ts="2024-01-01T01:00:00"))
    record(history_file, _entry("backup", exit_code=1, ts="2024-01-01T02:00:00"))
    result = check_escalation("backup", history_file, threshold=2)
    # Newest first: fail, ok, fail — streak is 1
    assert result.consecutive_failures == 1
    assert not result.should_escalate


def test_timed_out_counts_as_failure(history_file: Path) -> None:
    for i in range(2):
        record(history_file, _entry("backup", exit_code=0, timed_out=True, ts=f"2024-01-01T0{i}:00:00"))
    result = check_escalation("backup", history_file, threshold=2)
    assert result.consecutive_failures == 2
    assert result.should_escalate


def test_other_jobs_ignored(history_file: Path) -> None:
    for i in range(5):
        record(history_file, _entry("other", exit_code=1, ts=f"2024-01-01T0{i}:00:00"))
    record(history_file, _entry("backup", exit_code=0, ts="2024-01-01T06:00:00"))
    result = check_escalation("backup", history_file, threshold=3)
    assert result.consecutive_failures == 0
    assert not result.should_escalate


def test_invalid_threshold_raises(history_file: Path) -> None:
    with pytest.raises(ValueError):
        check_escalation("backup", history_file, threshold=0)
