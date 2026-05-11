"""Tests for cronwatch.ratelimit."""

from __future__ import annotations

import json
import time

import pytest

from cronwatch.ratelimit import (
    RateLimitEntry,
    clear_rate_limit,
    is_rate_limited,
    record_alert,
)


@pytest.fixture()
def rl_file(tmp_path):
    return tmp_path / "ratelimit.json"


_NOW = 1_700_000_000.0
_COOLDOWN = 300  # 5 minutes


# --- RateLimitEntry ---


def test_entry_is_cooling_down_within_window():
    entry = RateLimitEntry(job_name="backup", last_alerted_at=_NOW)
    assert entry.is_cooling_down(_COOLDOWN, now=_NOW + 60) is True


def test_entry_not_cooling_down_after_window():
    entry = RateLimitEntry(job_name="backup", last_alerted_at=_NOW)
    assert entry.is_cooling_down(_COOLDOWN, now=_NOW + 301) is False


def test_entry_not_cooling_down_at_exact_boundary():
    entry = RateLimitEntry(job_name="backup", last_alerted_at=_NOW)
    assert entry.is_cooling_down(_COOLDOWN, now=_NOW + 300) is False


# --- record_alert ---


def test_record_alert_creates_file(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    assert rl_file.exists()
    data = json.loads(rl_file.read_text())
    assert data["myjob"] == _NOW


def test_record_alert_overwrites_existing(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    record_alert(rl_file, "myjob", now=_NOW + 100)
    data = json.loads(rl_file.read_text())
    assert data["myjob"] == _NOW + 100


def test_record_alert_multiple_jobs(rl_file):
    record_alert(rl_file, "job_a", now=_NOW)
    record_alert(rl_file, "job_b", now=_NOW + 50)
    data = json.loads(rl_file.read_text())
    assert "job_a" in data and "job_b" in data


# --- is_rate_limited ---


def test_not_rate_limited_when_no_file(rl_file):
    assert is_rate_limited(rl_file, "myjob", _COOLDOWN, now=_NOW) is False


def test_not_rate_limited_when_job_not_recorded(rl_file):
    record_alert(rl_file, "other_job", now=_NOW)
    assert is_rate_limited(rl_file, "myjob", _COOLDOWN, now=_NOW + 10) is False


def test_rate_limited_within_cooldown(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    assert is_rate_limited(rl_file, "myjob", _COOLDOWN, now=_NOW + 60) is True


def test_not_rate_limited_after_cooldown(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    assert is_rate_limited(rl_file, "myjob", _COOLDOWN, now=_NOW + 301) is False


def test_zero_cooldown_never_rate_limits(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    assert is_rate_limited(rl_file, "myjob", 0, now=_NOW + 1) is False


# --- clear_rate_limit ---


def test_clear_returns_true_when_exists(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    assert clear_rate_limit(rl_file, "myjob") is True


def test_clear_removes_entry(rl_file):
    record_alert(rl_file, "myjob", now=_NOW)
    clear_rate_limit(rl_file, "myjob")
    assert is_rate_limited(rl_file, "myjob", _COOLDOWN, now=_NOW + 10) is False


def test_clear_returns_false_when_not_present(rl_file):
    assert clear_rate_limit(rl_file, "myjob") is False


def test_clear_does_not_affect_other_jobs(rl_file):
    record_alert(rl_file, "job_a", now=_NOW)
    record_alert(rl_file, "job_b", now=_NOW)
    clear_rate_limit(rl_file, "job_a")
    assert is_rate_limited(rl_file, "job_b", _COOLDOWN, now=_NOW + 10) is True
