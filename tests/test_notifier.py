"""Tests for cronwatch.notifier (including webhook dispatch)."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from cronwatch.notifier import dispatch, NotificationResult
from cronwatch.runner import JobResult
from cronwatch.config import AlertConfig
from cronwatch.webhook import WebhookResult


def _make_result(
    exit_code: int = 1,
    timed_out: bool = False,
    duration: float = 1.0,
) -> JobResult:
    return JobResult(exit_code=exit_code, stdout="", stderr="",
                     duration=duration, timed_out=timed_out)


def _make_alert_cfg(**kwargs) -> AlertConfig:
    defaults = {"email_to": None, "webhook_url": None}
    defaults.update(kwargs)
    return AlertConfig(**defaults)


def test_no_alert_when_job_succeeds():
    result = _make_result(exit_code=0)
    cfg = _make_alert_cfg(email_to="ops@example.com", webhook_url="http://hook")
    nr = dispatch("job", result, cfg)
    assert nr.nothing_sent()


def test_email_dispatched_on_failure():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg(email_to="ops@example.com")
    with patch("cronwatch.notifier.send_email_alert") as mock_email:
        nr = dispatch("job", result, cfg)
    mock_email.assert_called_once()
    assert nr.email_sent is True
    assert nr.webhook_sent is False


def test_webhook_dispatched_on_failure():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg(webhook_url="http://example.com/hook")
    ok_whr = WebhookResult(job_name="job", url="http://example.com/hook",
                            status_code=200, success=True)
    with patch("cronwatch.notifier.send_webhook", return_value=ok_whr) as mock_wh:
        nr = dispatch("job", result, cfg)
    mock_wh.assert_called_once()
    assert nr.webhook_sent is True
    assert nr.email_sent is False


def test_both_channels_dispatched():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg(email_to="ops@example.com",
                          webhook_url="http://example.com/hook")
    ok_whr = WebhookResult(job_name="job", url="http://example.com/hook",
                            status_code=200, success=True)
    with patch("cronwatch.notifier.send_email_alert"), \
         patch("cronwatch.notifier.send_webhook", return_value=ok_whr):
        nr = dispatch("job", result, cfg)
    assert nr.email_sent is True
    assert nr.webhook_sent is True
    assert nr.all_succeeded()


def test_email_error_captured():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg(email_to="ops@example.com")
    with patch("cronwatch.notifier.send_email_alert",
               side_effect=OSError("smtp down")):
        nr = dispatch("job", result, cfg)
    assert nr.email_sent is False
    assert "smtp down" in (nr.error or "")


def test_webhook_failure_reflected():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg(webhook_url="http://example.com/hook")
    fail_whr = WebhookResult(job_name="job", url="http://example.com/hook",
                              status_code=500, success=False, error="server error")
    with patch("cronwatch.notifier.send_webhook", return_value=fail_whr):
        nr = dispatch("job", result, cfg)
    assert nr.webhook_sent is False
    assert nr.webhook_result is not None
    assert nr.webhook_result.status_code == 500
