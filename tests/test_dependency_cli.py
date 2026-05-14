"""Tests for cronwatch.dependency_cli."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cronwatch.dependency_cli import cmd_dep_check, main
from cronwatch.dependency import DependencyReport, DependencyResult


def _make_args(config: str) -> MagicMock:
    ns = MagicMock()
    ns.config = config
    return ns


def _make_report(blocked: bool) -> DependencyReport:
    result = DependencyResult(
        job_name="job_a",
        blocked_by=["dep_x"] if blocked else [],
    )
    return DependencyReport(results=[result])


def test_cmd_dep_check_all_clear(tmp_path):
    cfg_path = str(tmp_path / "cronwatch.yml")
    report = _make_report(blocked=False)
    with patch("cronwatch.dependency_cli.CronwatchConfig.load") as mock_load, \
         patch("cronwatch.dependency_cli.check_all_dependencies", return_value=report):
        mock_cfg = MagicMock()
        mock_cfg.jobs = []
        mock_cfg.history_dir = str(tmp_path)
        mock_load.return_value = mock_cfg
        code = cmd_dep_check(_make_args(cfg_path))
    assert code == 0


def test_cmd_dep_check_blocked(tmp_path, capsys):
    cfg_path = str(tmp_path / "cronwatch.yml")
    report = _make_report(blocked=True)
    with patch("cronwatch.dependency_cli.CronwatchConfig.load") as mock_load, \
         patch("cronwatch.dependency_cli.check_all_dependencies", return_value=report):
        mock_cfg = MagicMock()
        mock_job = MagicMock()
        mock_job.name = "job_a"
        mock_job.depends_on = ["dep_x"]
        mock_cfg.jobs = [mock_job]
        mock_cfg.history_dir = str(tmp_path)
        mock_load.return_value = mock_cfg
        code = cmd_dep_check(_make_args(cfg_path))
    assert code == 1
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out


def test_cmd_dep_check_no_deps(tmp_path, capsys):
    cfg_path = str(tmp_path / "cronwatch.yml")
    with patch("cronwatch.dependency_cli.CronwatchConfig.load") as mock_load:
        mock_cfg = MagicMock()
        mock_cfg.jobs = []
        mock_load.return_value = mock_cfg
        code = cmd_dep_check(_make_args(cfg_path))
    assert code == 0
    captured = capsys.readouterr()
    assert "No job dependencies" in captured.out


def test_main_no_subcommand_prints_help(capsys):
    code = main([])
    assert code == 1


def test_main_dep_check_subcommand(tmp_path):
    report = _make_report(blocked=False)
    with patch("cronwatch.dependency_cli.CronwatchConfig.load") as mock_load, \
         patch("cronwatch.dependency_cli.check_all_dependencies", return_value=report):
        mock_cfg = MagicMock()
        mock_cfg.jobs = []
        mock_load.return_value = mock_cfg
        code = main(["dep-check", "-c", str(tmp_path / "cronwatch.yml")])
    assert code == 0
