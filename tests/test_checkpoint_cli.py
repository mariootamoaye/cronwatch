"""Tests for cronwatch.checkpoint_cli."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.checkpoint import record_checkpoint
from cronwatch.checkpoint_cli import (
    cmd_cp_add,
    cmd_cp_list,
    cmd_cp_last,
    cmd_cp_clear,
)


def _ns(cp_file: Path, **kwargs) -> argparse.Namespace:
    defaults = {"file": str(cp_file), "job": "backup", "name": "start", "note": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_cp_add_prints_confirmation(tmp_path: Path, capsys) -> None:
    cp_file = tmp_path / "cp.json"
    cmd_cp_add(_ns(cp_file))
    out = capsys.readouterr().out
    assert "Checkpoint recorded" in out
    assert "backup" in out
    assert "start" in out


def test_cmd_cp_list_shows_entries(tmp_path: Path, capsys) -> None:
    cp_file = tmp_path / "cp.json"
    record_checkpoint(cp_file, job="backup", name="start")
    record_checkpoint(cp_file, job="backup", name="done")
    cmd_cp_list(_ns(cp_file, job=None))
    out = capsys.readouterr().out
    assert "start" in out
    assert "done" in out


def test_cmd_cp_list_empty_message(tmp_path: Path, capsys) -> None:
    cp_file = tmp_path / "cp.json"
    cmd_cp_list(_ns(cp_file, job=None))
    assert "No checkpoints" in capsys.readouterr().out


def test_cmd_cp_last_prints_entry(tmp_path: Path, capsys) -> None:
    cp_file = tmp_path / "cp.json"
    record_checkpoint(cp_file, job="backup", name="done", note="ok")
    cmd_cp_last(_ns(cp_file))
    out = capsys.readouterr().out
    assert "done" in out
    assert "ok" in out


def test_cmd_cp_last_exits_when_missing(tmp_path: Path) -> None:
    cp_file = tmp_path / "cp.json"
    with pytest.raises(SystemExit) as exc:
        cmd_cp_last(_ns(cp_file))
    assert exc.value.code == 1


def test_cmd_cp_clear_removes_entries(tmp_path: Path, capsys) -> None:
    cp_file = tmp_path / "cp.json"
    record_checkpoint(cp_file, job="backup", name="start")
    cmd_cp_clear(_ns(cp_file))
    out = capsys.readouterr().out
    assert "Removed 1" in out
