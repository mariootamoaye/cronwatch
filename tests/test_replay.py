"""Tests for cronwatch.replay."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.deadletter import DeadLetterEntry
from cronwatch.replay import ReplayReport, ReplayResult, replay_job, run_replay
from cronwatch.runner import JobResult


def _make_entry(job_name: str = "backup", ts: str = "2024-01-01T00:00:00") -> DeadLetterEntry:
    return DeadLetterEntry(id="abc123", job_name=job_name, timestamp=ts, reason="exit 1", payload={})


def _make_job_cfg(name: str = "backup") -> MagicMock:
    cfg = MagicMock()
    cfg.name = name
    return cfg


def _make_job_result(success: bool = True, exit_code: int = 0) -> JobResult:
    return JobResult(
        job_name="backup",
        success=success,
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=1.0,
        timed_out=False,
    )


def test_replay_result_str_ok():
    r = ReplayResult(job_name="backup", original_ts="2024-01-01T00:00:00", success=True, exit_code=0)
    assert "ok" in str(r)
    assert "backup" in str(r)


def test_replay_result_str_failed():
    r = ReplayResult(job_name="backup", original_ts="2024-01-01T00:00:00", success=False, exit_code=1)
    assert "FAILED" in str(r)


def test_replay_report_all_ok():
    report = ReplayReport(results=[
        ReplayResult(job_name="a", original_ts="t", success=True, exit_code=0),
        ReplayResult(job_name="b", original_ts="t", success=True, exit_code=0),
    ])
    assert report.all_ok is True
    assert report.succeeded == 2
    assert report.failed == 0


def test_replay_report_with_failure():
    report = ReplayReport(results=[
        ReplayResult(job_name="a", original_ts="t", success=True, exit_code=0),
        ReplayResult(job_name="b", original_ts="t", success=False, exit_code=1),
    ])
    assert report.all_ok is False
    assert report.failed == 1


def test_replay_job_success():
    entry = _make_entry()
    cfg = _make_job_cfg()
    job_result = _make_job_result(success=True)
    with patch("cronwatch.replay.run_job", return_value=job_result):
        result = replay_job(entry, cfg)
    assert result.success is True
    assert result.job_name == "backup"


def test_replay_job_failure():
    entry = _make_entry()
    cfg = _make_job_cfg()
    job_result = _make_job_result(success=False, exit_code=1)
    with patch("cronwatch.replay.run_job", return_value=job_result):
        result = replay_job(entry, cfg)
    assert result.success is False
    assert result.exit_code == 1


def test_replay_job_exception_captured():
    entry = _make_entry()
    cfg = _make_job_cfg()
    with patch("cronwatch.replay.run_job", side_effect=RuntimeError("boom")):
        result = replay_job(entry, cfg)
    assert result.success is False
    assert "boom" in result.error


def test_run_replay_skips_unknown_jobs(tmp_path):
    dl_path = str(tmp_path / "dl.json")
    entry = _make_entry(job_name="unknown")
    entries_data = [json.dumps(entry.to_dict())]
    Path(dl_path).write_text("\n".join(entries_data))
    report = run_replay(dl_path, {})
    assert report.total == 0


def test_run_replay_purges_on_success(tmp_path):
    dl_path = str(tmp_path / "dl.json")
    entry = _make_entry(job_name="backup")
    Path(dl_path).write_text(json.dumps(entry.to_dict()) + "\n")
    cfg = _make_job_cfg("backup")
    job_result = _make_job_result(success=True)
    with patch("cronwatch.replay.run_job", return_value=job_result), \
         patch("cronwatch.replay.list_entries", return_value=[entry]), \
         patch("cronwatch.replay.remove_entry") as mock_remove:
        report = run_replay(dl_path, {"backup": cfg}, purge_on_success=True)
    assert report.succeeded == 1
    mock_remove.assert_called_once_with(dl_path, entry.id)


def test_run_replay_keep_flag_does_not_purge(tmp_path):
    dl_path = str(tmp_path / "dl.json")
    entry = _make_entry(job_name="backup")
    cfg = _make_job_cfg("backup")
    job_result = _make_job_result(success=True)
    with patch("cronwatch.replay.run_job", return_value=job_result), \
         patch("cronwatch.replay.list_entries", return_value=[entry]), \
         patch("cronwatch.replay.remove_entry") as mock_remove:
        run_replay(dl_path, {"backup": cfg}, purge_on_success=False)
    mock_remove.assert_not_called()
