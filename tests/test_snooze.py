"""Tests for cronwatch.snooze and cronwatch.snooze_cli."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.snooze import (
    SnoozeEntry,
    clear_snooze,
    is_snoozed,
    load_all,
    snooze_job,
)
from cronwatch.snooze_cli import _parse_duration, cmd_snooze, cmd_unsnooze, cmd_snooze_list


_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
_FUTURE = _NOW + timedelta(hours=2)
_PAST = _NOW - timedelta(hours=1)


@pytest.fixture()
def snooze_file(tmp_path: Path) -> Path:
    return tmp_path / "snooze.json"


# ---------------------------------------------------------------------------
# SnoozeEntry
# ---------------------------------------------------------------------------

def test_snooze_entry_active():
    entry = SnoozeEntry(job_name="backup", until=_FUTURE)
    assert entry.is_active(_NOW) is True


def test_snooze_entry_expired():
    entry = SnoozeEntry(job_name="backup", until=_PAST)
    assert entry.is_active(_NOW) is False


# ---------------------------------------------------------------------------
# snooze_job / is_snoozed / clear_snooze
# ---------------------------------------------------------------------------

def test_snooze_job_creates_file(snooze_file: Path):
    snooze_job("myjob", _FUTURE, path=snooze_file)
    assert snooze_file.exists()
    data = json.loads(snooze_file.read_text())
    assert "myjob" in data


def test_is_snoozed_active(snooze_file: Path):
    snooze_job("myjob", _FUTURE, path=snooze_file)
    assert is_snoozed("myjob", now=_NOW, path=snooze_file) is True


def test_is_snoozed_expired(snooze_file: Path):
    snooze_job("myjob", _PAST, path=snooze_file)
    assert is_snoozed("myjob", now=_NOW, path=snooze_file) is False


def test_is_snoozed_missing_job(snooze_file: Path):
    assert is_snoozed("ghost", now=_NOW, path=snooze_file) is False


def test_clear_snooze_removes_entry(snooze_file: Path):
    snooze_job("myjob", _FUTURE, path=snooze_file)
    removed = clear_snooze("myjob", path=snooze_file)
    assert removed is True
    assert is_snoozed("myjob", now=_NOW, path=snooze_file) is False


def test_clear_snooze_returns_false_when_absent(snooze_file: Path):
    assert clear_snooze("ghost", path=snooze_file) is False


def test_load_all_returns_entries(snooze_file: Path):
    snooze_job("job_a", _FUTURE, path=snooze_file)
    snooze_job("job_b", _PAST, path=snooze_file)
    entries = load_all(path=snooze_file)
    assert set(entries.keys()) == {"job_a", "job_b"}


# ---------------------------------------------------------------------------
# snooze_cli helpers
# ---------------------------------------------------------------------------

def test_parse_duration_hours():
    assert _parse_duration("3h") == timedelta(hours=3)


def test_parse_duration_minutes():
    assert _parse_duration("45m") == timedelta(minutes=45)


def test_parse_duration_days():
    assert _parse_duration("2d") == timedelta(days=2)


class _NS:
    """Minimal argparse.Namespace stand-in."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_cmd_snooze_writes_entry(snooze_file: Path, capsys):
    rc = cmd_snooze(_NS(job="deploy", duration="1h"), path=snooze_file)
    assert rc == 0
    assert is_snoozed("deploy", path=snooze_file)
    assert "deploy" in capsys.readouterr().out


def test_cmd_unsnooze_clears_entry(snooze_file: Path):
    snooze_job("deploy", _FUTURE, path=snooze_file)
    rc = cmd_unsnooze(_NS(job="deploy"), path=snooze_file)
    assert rc == 0
    assert not is_snoozed("deploy", path=snooze_file)


def test_cmd_unsnooze_returns_1_when_absent(snooze_file: Path):
    rc = cmd_unsnooze(_NS(job="ghost"), path=snooze_file)
    assert rc == 1


def test_cmd_snooze_list_empty(snooze_file: Path, capsys):
    rc = cmd_snooze_list(_NS(), path=snooze_file)
    assert rc == 0
    assert "No snoozes" in capsys.readouterr().out


def test_cmd_snooze_list_shows_entries(snooze_file: Path, capsys):
    snooze_job("job_x", _FUTURE, path=snooze_file)
    cmd_snooze_list(_NS(), path=snooze_file)
    out = capsys.readouterr().out
    assert "job_x" in out
    assert "active" in out
