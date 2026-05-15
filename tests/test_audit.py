"""Tests for cronwatch.audit and cronwatch.audit_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.audit import AuditEntry, list_entries, record
from cronwatch.audit_cli import cmd_audit_list


@pytest.fixture()
def audit_file(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


# ---------------------------------------------------------------------------
# AuditEntry serialisation
# ---------------------------------------------------------------------------

def test_to_dict_round_trip():
    e = AuditEntry(timestamp="2024-01-01T00:00:00+00:00", actor="cli",
                   action="snooze", target="backup", detail="2h")
    assert AuditEntry.from_dict(e.to_dict()) == e


def test_from_dict_optional_fields():
    e = AuditEntry.from_dict({"timestamp": "t", "actor": "a", "action": "x"})
    assert e.target is None
    assert e.detail is None


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------

def test_record_creates_file(audit_file: Path):
    record("cli", "snooze", target="job1", path=audit_file)
    assert audit_file.exists()


def test_record_appends_entries(audit_file: Path):
    record("cli", "snooze", target="job1", path=audit_file)
    record("scheduler", "config_reload", path=audit_file)
    lines = [l for l in audit_file.read_text().splitlines() if l.strip()]
    assert len(lines) == 2


def test_record_returns_entry(audit_file: Path):
    entry = record("cli", "mute", target="job2", detail="1d", path=audit_file)
    assert entry.actor == "cli"
    assert entry.action == "mute"
    assert entry.target == "job2"


def test_record_timestamp_is_iso(audit_file: Path):
    entry = record("cli", "test", path=audit_file)
    assert "T" in entry.timestamp
    assert "+" in entry.timestamp or "Z" in entry.timestamp


# ---------------------------------------------------------------------------
# list_entries()
# ---------------------------------------------------------------------------

def test_list_entries_empty_when_no_file(audit_file: Path):
    assert list_entries(path=audit_file) == []


def test_list_entries_returns_all(audit_file: Path):
    record("cli", "snooze", path=audit_file)
    record("cli", "mute", path=audit_file)
    assert len(list_entries(path=audit_file)) == 2


def test_list_entries_filter_by_actor(audit_file: Path):
    record("cli", "snooze", path=audit_file)
    record("scheduler", "config_reload", path=audit_file)
    result = list_entries(path=audit_file, actor="cli")
    assert len(result) == 1
    assert result[0].actor == "cli"


def test_list_entries_filter_by_action(audit_file: Path):
    record("cli", "snooze", path=audit_file)
    record("cli", "mute", path=audit_file)
    result = list_entries(path=audit_file, action="mute")
    assert len(result) == 1
    assert result[0].action == "mute"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class _NS:
    def __init__(self, file, actor="", action=""):
        self.file = str(file)
        self.actor = actor
        self.action = action


def test_cmd_audit_list_no_entries(audit_file: Path, capsys):
    rc = cmd_audit_list(_NS(audit_file))
    assert rc == 0
    assert "No audit entries" in capsys.readouterr().out


def test_cmd_audit_list_shows_entries(audit_file: Path, capsys):
    record("cli", "snooze", target="job1", path=audit_file)
    rc = cmd_audit_list(_NS(audit_file))
    assert rc == 0
    out = capsys.readouterr().out
    assert "snooze" in out
    assert "job1" in out


def test_cmd_audit_list_filter(audit_file: Path, capsys):
    record("cli", "snooze", path=audit_file)
    record("scheduler", "config_reload", path=audit_file)
    rc = cmd_audit_list(_NS(audit_file, actor="scheduler"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "config_reload" in out
    assert "snooze" not in out
