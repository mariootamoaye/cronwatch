"""Tests for cronwatch.replay_render."""
from __future__ import annotations

from cronwatch.replay import ReplayReport, ReplayResult
from cronwatch.replay_render import render_replay_table


def _result(name: str = "backup", success: bool = True, exit_code: int = 0) -> ReplayResult:
    return ReplayResult(
        job_name=name,
        original_ts="2024-06-01T12:00:00",
        success=success,
        exit_code=exit_code,
    )


def test_render_empty_report():
    report = ReplayReport(results=[])
    output = render_replay_table(report)
    assert "No entries" in output


def test_render_includes_header():
    report = ReplayReport(results=[_result()])
    output = render_replay_table(report)
    assert "JOB" in output
    assert "STATUS" in output
    assert "EXIT" in output


def test_render_shows_ok_status():
    report = ReplayReport(results=[_result(success=True)])
    output = render_replay_table(report)
    assert "ok" in output


def test_render_shows_failed_status():
    report = ReplayReport(results=[_result(success=False, exit_code=1)])
    output = render_replay_table(report)
    assert "FAILED" in output


def test_render_shows_job_name():
    report = ReplayReport(results=[_result(name="db-dump")])
    output = render_replay_table(report)
    assert "db-dump" in output


def test_render_shows_summary_line():
    report = ReplayReport(results=[
        _result(success=True),
        _result(name="other", success=False, exit_code=2),
    ])
    output = render_replay_table(report)
    assert "Total: 2" in output
    assert "Succeeded: 1" in output
    assert "Failed: 1" in output


def test_render_shows_error_note():
    result = ReplayResult(
        job_name="broken",
        original_ts="2024-06-01T12:00:00",
        success=False,
        exit_code=-1,
        error="connection refused",
    )
    report = ReplayReport(results=[result])
    output = render_replay_table(report)
    assert "connection refused" in output
