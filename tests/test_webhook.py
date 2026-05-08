"""Tests for cronwatch.webhook."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from cronwatch.webhook import send_webhook, _build_payload
from cronwatch.runner import JobResult
from cronwatch.config import AlertConfig


def _make_result(
    exit_code: int = 0,
    stdout: str = "",
    stderr: str = "",
    duration: float = 1.0,
    timed_out: bool = False,
) -> JobResult:
    return JobResult(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration=duration,
        timed_out=timed_out,
    )


def _make_alert_cfg(webhook_url: str = "http://example.com/hook") -> AlertConfig:
    return AlertConfig(webhook_url=webhook_url)


def test_build_payload_fields():
    result = _make_result(exit_code=1, stdout="out", stderr="err", duration=2.5)
    payload = _build_payload("myjob", result)
    assert payload["job"] == "myjob"
    assert payload["exit_code"] == 1
    assert payload["stdout"] == "out"
    assert payload["stderr"] == "err"
    assert payload["duration_seconds"] == 2.5
    assert payload["timed_out"] is False


def test_no_url_returns_error():
    result = _make_result()
    cfg = AlertConfig(webhook_url=None)
    whr = send_webhook("job", result, cfg)
    assert whr.success is False
    assert "No webhook URL" in (whr.error or "")


def test_successful_post():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        whr = send_webhook("myjob", result, cfg)
    assert whr.success is True
    assert whr.status_code == 200
    assert whr.job_name == "myjob"


def test_http_error_returns_failure():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg()
    with patch("urllib.request.urlopen",
               side_effect=urllib.error.HTTPError(url=None, code=500,
                                                   msg="Server Error", hdrs=None, fp=None)):
        whr = send_webhook("myjob", result, cfg)
    assert whr.success is False
    assert whr.status_code == 500


def test_connection_error_returns_failure():
    result = _make_result(exit_code=1)
    cfg = _make_alert_cfg()
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        whr = send_webhook("myjob", result, cfg)
    assert whr.success is False
    assert whr.status_code is None
    assert "connection refused" in (whr.error or "")
