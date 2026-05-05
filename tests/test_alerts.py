"""Tests for cronwatch.alerts module."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from cronwatch.config import AlertConfig
from cronwatch.runner import JobResult
from cronwatch.alerts import should_alert, send_email_alert, _build_subject, _build_body


def make_result(exit_code=0, timed_out=False, duration=1.0):
    return JobResult(
        job_name="backup",
        command="/usr/bin/backup.sh",
        exit_code=exit_code,
        stdout="done",
        stderr="" if exit_code == 0 else "error occurred",
        duration_seconds=duration,
        started_at=datetime(2024, 1, 1, 12, 0, 0),
        finished_at=datetime(2024, 1, 1, 12, 0, 1),
        timed_out=timed_out,
    )


def make_alert_cfg():
    return AlertConfig(
        to_emails=["admin@example.com"],
        from_email="cronwatch@example.com",
        smtp_host="localhost",
        smtp_port=25,
    )


def test_should_alert_on_failure():
    assert should_alert(make_result(exit_code=1), max_duration=None) is True


def test_should_alert_on_timeout():
    assert should_alert(make_result(timed_out=True), max_duration=None) is True


def test_should_alert_on_slow_job():
    assert should_alert(make_result(duration=120.0), max_duration=60.0) is True


def test_no_alert_on_success():
    assert should_alert(make_result(), max_duration=None) is False


def test_no_alert_on_fast_success():
    assert should_alert(make_result(duration=5.0), max_duration=60.0) is False


def test_build_subject_failure():
    subject = _build_subject(make_result(exit_code=2), max_duration=None)
    assert "FAILED" in subject
    assert "backup" in subject


def test_build_subject_timeout():
    subject = _build_subject(make_result(timed_out=True), max_duration=None)
    assert "TIMEOUT" in subject


def test_build_subject_slow():
    subject = _build_subject(make_result(duration=90.0), max_duration=60.0)
    assert "SLOW" in subject


def test_build_body_contains_fields():
    body = _build_body(make_result())
    assert "backup" in body
    assert "/usr/bin/backup.sh" in body
    assert "done" in body


def test_send_email_alert():
    result = make_result(exit_code=1)
    cfg = make_alert_cfg()
    with patch("cronwatch.alerts.smtplib.SMTP") as mock_smtp_cls:
        mock_smtp = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_smtp
        send_email_alert(result, cfg, max_duration=None)
        mock_smtp.send_message.assert_called_once()
