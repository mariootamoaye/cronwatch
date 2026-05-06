"""Tests for cronwatch.report."""
from __future__ import annotations

import pytest

from cronwatch.runner import JobResult
from cronwatch.scheduler import SchedulerResult
from cronwatch.summary import build_summary
from cronwatch.report import build_report, Report


def _make_result(
    name: str = "job",
    returncode: int = 0,
    duration: float = 1.0,
    timed_out: bool = False,
    exceeded_max_duration: bool = False,
) -> JobResult:
    return JobResult(
        job_name=name,
        returncode=returncode,
        stdout="",
        stderr="",
        duration_s=duration,
        timed_out=timed_out,
        exceeded_max_duration=exceeded_max_duration,
    )


def _make_scheduler_result(results):
    return SchedulerResult(results=results)


def test_report_all_ok():
    sr = _make_scheduler_result([_make_result("backup", 0, 2.5)])
    summary = build_summary(sr)
    report = build_report(summary)
    assert report.all_ok
    assert report.total == 1
    assert report.ok_count == 1
    assert report.failed_count == 0


def test_report_with_failure():
    sr = _make_scheduler_result([
        _make_result("backup", 0, 2.5),
        _make_result("sync", 1, 0.5),
    ])
    summary = build_summary(sr)
    report = build_report(summary)
    assert not report.all_ok
    assert report.total == 2
    assert report.ok_count == 1
    assert report.failed_count == 1


def test_report_line_note_timeout():
    sr = _make_scheduler_result([_make_result("job", 1, 30.0, timed_out=True)])
    summary = build_summary(sr)
    report = build_report(summary)
    assert report.lines[0].note == "timed out"


def test_report_line_note_exceeded_duration():
    sr = _make_scheduler_result(
        [_make_result("job", 0, 120.0, exceeded_max_duration=True)]
    )
    summary = build_summary(sr)
    report = build_report(summary)
    assert report.lines[0].note == "exceeded max duration"


def test_report_line_note_failed():
    sr = _make_scheduler_result([_make_result("job", 2, 1.0)])
    summary = build_summary(sr)
    report = build_report(summary)
    assert report.lines[0].note == "non-zero exit"


def test_report_as_text_contains_job_name():
    sr = _make_scheduler_result([_make_result("nightly-backup", 0, 5.0)])
    summary = build_summary(sr)
    report = build_report(summary)
    text = report.as_text()
    assert "nightly-backup" in text
    assert "OK" in text
    assert "Total: 1" in text


def test_report_as_text_shows_failed_count():
    sr = _make_scheduler_result([
        _make_result("a", 0, 1.0),
        _make_result("b", 1, 1.0),
        _make_result("c", 1, 1.0),
    ])
    summary = build_summary(sr)
    report = build_report(summary)
    text = report.as_text()
    assert "Failed: 2" in text
    assert "OK: 1" in text
