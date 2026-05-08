"""Tests for cronwatch.mute_cli."""
from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.mute import mute_job
from cronwatch.mute_cli import (
    _parse_duration,
    build_mute_parser,
    cmd_mute,
    cmd_mute_list,
    cmd_unmute,
)

_FUTURE_ISO = "2099-01-01T00:00:00+00:00"


@pytest.fixture()
def mute_file(tmp_path: Path) -> Path:
    return tmp_path / "mutes.json"


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


# --- _parse_duration ---

def test_parse_duration_minutes():
    assert _parse_duration("30m") == timedelta(minutes=30)


def test_parse_duration_hours():
    assert _parse_duration("2h") == timedelta(hours=2)


def test_parse_duration_days():
    assert _parse_duration("1d") == timedelta(days=1)


def test_parse_duration_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_duration("5x")


# --- cmd_mute ---

def test_cmd_mute_creates_entry(mute_file: Path, capsys):
    ns = _ns(job="backup", duration=timedelta(hours=1), reason="")
    rc = cmd_mute(ns, path=mute_file)
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out
    assert "Muted" in out


# --- cmd_unmute ---

def test_cmd_unmute_existing(mute_file: Path, capsys):
    from datetime import datetime, timezone
    mute_job("backup", datetime(2099, 1, 1, tzinfo=timezone.utc), path=mute_file)
    ns = _ns(job="backup")
    rc = cmd_unmute(ns, path=mute_file)
    assert rc == 0
    assert "Unmuted" in capsys.readouterr().out


def test_cmd_unmute_missing(mute_file: Path, capsys):
    ns = _ns(job="ghost")
    rc = cmd_unmute(ns, path=mute_file)
    assert rc == 0
    assert "No active mute" in capsys.readouterr().out


# --- cmd_mute_list ---

def test_cmd_mute_list_empty(mute_file: Path, capsys):
    ns = _ns()
    rc = cmd_mute_list(ns, path=mute_file)
    assert rc == 0
    assert "No active mutes" in capsys.readouterr().out


def test_cmd_mute_list_shows_entries(mute_file: Path, capsys):
    from datetime import datetime, timezone
    mute_job("backup", datetime(2099, 1, 1, tzinfo=timezone.utc), reason="maint", path=mute_file)
    ns = _ns()
    cmd_mute_list(ns, path=mute_file)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "maint" in out


# --- build_mute_parser ---

def test_build_mute_parser_registers_subcommands():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_mute_parser(sub)
    args = parser.parse_args(["mute", "backup", "1h"])
    assert args.job == "backup"
    assert args.duration == timedelta(hours=1)
