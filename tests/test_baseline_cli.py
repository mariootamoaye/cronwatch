"""Tests for cronwatch.baseline_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from cronwatch.baseline_cli import (
    cmd_baseline_check,
    cmd_baseline_dump,
    cmd_baseline_record,
    cmd_baseline_stats,
)


def _ns(baseline_file: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(baseline_file=str(baseline_file), **kwargs)


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# cmd_baseline_record
# ---------------------------------------------------------------------------

def test_cmd_baseline_record_creates_file(tmp_path: Path, capsys):
    bf = tmp_path / "b.json"
    cmd_baseline_record(_ns(bf, job="sync", duration=15.0))
    assert bf.exists()
    out = capsys.readouterr().out
    assert "sync" in out
    assert "15.00" in out


# ---------------------------------------------------------------------------
# cmd_baseline_stats
# ---------------------------------------------------------------------------

def test_cmd_baseline_stats_no_data(tmp_path: Path, capsys):
    bf = tmp_path / "b.json"
    cmd_baseline_stats(_ns(bf, job="sync"))
    out = capsys.readouterr().out
    assert "No baseline data" in out


def test_cmd_baseline_stats_shows_values(tmp_path: Path, capsys):
    bf = tmp_path / "b.json"
    _write(bf, {"sync": [10.0, 20.0, 30.0]})
    cmd_baseline_stats(_ns(bf, job="sync"))
    out = capsys.readouterr().out
    assert "Mean" in out
    assert "Std dev" in out
    assert "Upper bound" in out


# ---------------------------------------------------------------------------
# cmd_baseline_check
# ---------------------------------------------------------------------------

def test_cmd_baseline_check_ok(tmp_path: Path, capsys):
    bf = tmp_path / "b.json"
    _write(bf, {"j": [10.0, 10.0, 10.0, 10.0]})
    cmd_baseline_check(_ns(bf, job="j", duration=10.0))
    out = capsys.readouterr().out
    assert "OK" in out


def test_cmd_baseline_check_anomalous(tmp_path: Path, capsys):
    bf = tmp_path / "b.json"
    _write(bf, {"j": [10.0, 10.0, 10.0, 10.0, 10.0]})
    cmd_baseline_check(_ns(bf, job="j", duration=9999.0))
    out = capsys.readouterr().out
    assert "ANOMALOUS" in out


# ---------------------------------------------------------------------------
# cmd_baseline_dump
# ---------------------------------------------------------------------------

def test_cmd_baseline_dump_no_file(tmp_path: Path, capsys):
    bf = tmp_path / "missing.json"
    cmd_baseline_dump(_ns(bf))
    out = capsys.readouterr().out
    assert "No baseline file" in out


def test_cmd_baseline_dump_shows_jobs(tmp_path: Path, capsys):
    bf = tmp_path / "b.json"
    _write(bf, {"alpha": [1.0, 2.0], "beta": [5.0]})
    cmd_baseline_dump(_ns(bf))
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out
