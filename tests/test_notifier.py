"""Tests for cronwatch.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig
from cronwatch.notifier import NotificationResult, dispatch
from cronwatch.runner import JobResult


def _make_result(
    exit_code: int = 0,
    timed_out: bool = False,
    duration: float = 1.0,
    max_duration: float | None = None,
) -> JobResult:
    return JobResult(
        job_name="test-job",
        command="echo hi",
        exit_code=exit_code,
        stdout="",
        stderr="",
        duration=duration,
        timed_out=timed_out,
        max_duration=max_duration,
    )


def _make_alert_cfg(email: str | None = "ops@example.com") -> AlertConfig:
    return AlertConfig(
        email=email,
        smtp_host="localhost",
        smtp_port=25,
        from_address="cron@example.com",
        on_failure=True,
        on_timeout=True,
        on_slow=False,
    )


def test_no_alert_when_job_succeeds():
    result = dispatch(_make_result(exit_code=0), _make_alert_cfg())
    assert result.nothing_sent
    assert result.all_succeeded is False  # nothing attempted


@patch("cronwatch.notifier.send_email_alert")
def test_email_dispatched_on_failure(mock_send):
    result = dispatch(_make_result(exit_code=1), _make_alert_cfg())
    mock_send.assert_called_once()
    assert "email" in result.channels_succeeded
    assert result.all_succeeded


@patch("cronwatch.notifier.send_email_alert")
def test_email_dispatched_on_timeout(mock_send):
    result = dispatch(_make_result(timed_out=True), _make_alert_cfg())
    mock_send.assert_called_once()
    assert "email" in result.channels_succeeded


@patch("cronwatch.notifier.send_email_alert", side_effect=OSError("connection refused"))
def test_email_error_recorded(mock_send):
    result = dispatch(_make_result(exit_code=1), _make_alert_cfg())
    assert "email" in result.channels_attempted
    assert "email" not in result.channels_succeeded
    assert any("email" in e for e in result.errors)
    assert result.all_succeeded is False


def test_no_email_channel_configured():
    cfg = _make_alert_cfg(email=None)
    result = dispatch(_make_result(exit_code=1), cfg)
    assert result.nothing_sent


def test_notification_result_defaults():
    nr = NotificationResult(job_name="myjob")
    assert nr.nothing_sent
    assert not nr.all_succeeded
    assert nr.errors == []


@patch("cronwatch.notifier.send_email_alert")
def test_slow_job_not_alerted_when_on_slow_disabled(mock_send):
    """Verify that a slow (but successful) job does not trigger an alert
    when on_slow is False in the alert configuration.
    """
    # duration exceeds max_duration, but on_slow=False so no alert expected
    result = dispatch(
        _make_result(exit_code=0, duration=120.0, max_duration=60.0),
        _make_alert_cfg(),
    )
    mock_send.assert_not_called()
    assert result.nothing_sent
