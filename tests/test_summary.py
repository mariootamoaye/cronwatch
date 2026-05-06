"""Tests for cronwatch.summary module."""

from unittest.mock import patch

import pytest

from cronwatch.runner import JobResult
from cronwatch.scheduler import SchedulerResult
from cronwatch.summary import (
    RunSummary,
    SummaryLine,
    build_summary,
    format_summary,
    _status_for,
)


def _make_result(
    returncode: int = 0,
    duration_s: float = 1.0,
    timed_out: bool = False,
    duration_exceeded: bool = False,
) -> JobResult:
    return JobResult(
        returncode=returncode,
        stdout="",
        stderr="",
        duration_s=duration_s,
        timed_out=timed_out,
        duration_exceeded=duration_exceeded,
    )


def _make_scheduler_result(results: dict) -> SchedulerResult:
    return SchedulerResult(results=results)


def test_status_ok():
    r = _make_result(returncode=0)
    status, note = _status_for(r)
    assert status == "OK"
    assert note == ""


def test_status_failed():
    r = _make_result(returncode=1)
    status, note = _status_for(r)
    assert status == "FAILED"
    assert "1" in note


def test_status_timeout():
    r = _make_result(returncode=-1, timed_out=True)
    status, note = _status_for(r)
    assert status == "TIMEOUT"


def test_status_slow():
    r = _make_result(returncode=0, duration_exceeded=True, duration_s=120.0)
    status, note = _status_for(r)
    assert status == "SLOW"
    assert "120" in note


def test_build_summary_all_ok():
    sr = _make_scheduler_result({"job_a": _make_result(), "job_b": _make_result()})
    summary = build_summary(sr)
    assert summary.total == 2
    assert summary.passed == 2
    assert summary.failed == 0
    assert summary.all_ok is True


def test_build_summary_with_failure():
    sr = _make_scheduler_result(
        {"good": _make_result(returncode=0), "bad": _make_result(returncode=2)}
    )
    summary = build_summary(sr)
    assert summary.failed == 1
    assert summary.passed == 1
    assert summary.all_ok is False


def test_build_summary_line_fields():
    sr = _make_scheduler_result({"myjob": _make_result(returncode=0, duration_s=3.5)})
    summary = build_summary(sr)
    line = summary.lines[0]
    assert line.job_name == "myjob"
    assert line.status == "OK"
    assert line.duration_s == pytest.approx(3.5)
    assert line.exit_code == 0


def test_format_summary_contains_job_name():
    sr = _make_scheduler_result({"backup": _make_result()})
    summary = build_summary(sr)
    text = format_summary(summary)
    assert "backup" in text
    assert "OK" in text


def test_format_summary_contains_totals():
    sr = _make_scheduler_result(
        {"a": _make_result(), "b": _make_result(returncode=1)}
    )
    summary = build_summary(sr)
    text = format_summary(summary)
    assert "Total: 2" in text
    assert "Failed: 1" in text
