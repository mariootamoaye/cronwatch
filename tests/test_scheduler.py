"""Tests for cronwatch.scheduler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig, CronwatchConfig, JobConfig
from cronwatch.runner import JobResult
from cronwatch.scheduler import SchedulerResult, run_all


def _make_config(*commands: str, max_duration: int | None = None) -> CronwatchConfig:
    jobs = [
        JobConfig(name=f"job{i}", command=cmd, max_duration=max_duration)
        for i, cmd in enumerate(commands)
    ]
    alerts = AlertConfig(
        smtp_host="localhost",
        from_addr="from@example.com",
        to_addrs=["to@example.com"],
    )
    return CronwatchConfig(jobs=jobs, alerts=alerts)


def _ok_result(name: str) -> JobResult:
    return JobResult(job_name=name, command="echo ok", returncode=0, duration=0.1)


def _fail_result(name: str) -> JobResult:
    return JobResult(job_name=name, command="false", returncode=1, duration=0.1)


# ---------------------------------------------------------------------------
# SchedulerResult helpers
# ---------------------------------------------------------------------------

def test_scheduler_result_all_ok():
    sr = SchedulerResult(results=[_ok_result("a"), _ok_result("b")])
    assert sr.all_ok is True
    assert sr.failed == []


def test_scheduler_result_with_failures():
    sr = SchedulerResult(results=[_ok_result("a"), _fail_result("b")])
    assert sr.all_ok is False
    assert len(sr.failed) == 1


# ---------------------------------------------------------------------------
# run_all
# ---------------------------------------------------------------------------

@patch("cronwatch.scheduler.send_email_alert")
@patch("cronwatch.scheduler.should_alert", return_value=False)
@patch("cronwatch.scheduler.run_job")
def test_run_all_no_alerts(mock_run, mock_should, mock_send):
    config = _make_config("echo hello", "echo world")
    mock_run.side_effect = [_ok_result("job0"), _ok_result("job1")]

    sr = run_all(config)

    assert mock_run.call_count == 2
    mock_send.assert_not_called()
    assert sr.all_ok is True


@patch("cronwatch.scheduler.send_email_alert")
@patch("cronwatch.scheduler.should_alert", return_value=True)
@patch("cronwatch.scheduler.run_job")
def test_run_all_sends_alert(mock_run, mock_should, mock_send):
    config = _make_config("false")
    mock_run.return_value = _fail_result("job0")

    sr = run_all(config)

    mock_send.assert_called_once()
    assert not sr.all_ok


@patch("cronwatch.scheduler.send_email_alert")
@patch("cronwatch.scheduler.should_alert", return_value=True)
@patch("cronwatch.scheduler.run_job")
def test_run_all_dry_run_skips_alert(mock_run, mock_should, mock_send):
    config = _make_config("false")
    mock_run.return_value = _fail_result("job0")

    run_all(config, dry_run=True)

    mock_send.assert_not_called()
