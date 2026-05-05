"""Tests for cronwatch.cli."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.cli import main
from cronwatch.scheduler import SchedulerResult
from cronwatch.runner import JobResult


def _ok_sr() -> SchedulerResult:
    return SchedulerResult(
        results=[JobResult(job_name="j", command="echo", returncode=0, duration=0.1)]
    )


def _fail_sr() -> SchedulerResult:
    r = JobResult(job_name="j", command="false", returncode=1, duration=0.1)
    return SchedulerResult(results=[r])


@patch("cronwatch.cli.run_all", return_value=_ok_sr())
@patch("cronwatch.cli.load_config")
def test_main_success(mock_load, mock_run, tmp_path):
    cfg_file = tmp_path / "cw.yml"
    cfg_file.write_text("jobs: []\n")
    mock_load.return_value = MagicMock()

    code = main(["-c", str(cfg_file)])

    assert code == 0
    mock_load.assert_called_once_with(cfg_file)


@patch("cronwatch.cli.run_all", return_value=_fail_sr())
@patch("cronwatch.cli.load_config")
def test_main_failure_exit_code(mock_load, mock_run, tmp_path):
    cfg_file = tmp_path / "cw.yml"
    cfg_file.write_text("jobs: []\n")
    mock_load.return_value = MagicMock()

    code = main(["-c", str(cfg_file)])

    assert code == 1


@patch("cronwatch.cli.load_config", side_effect=FileNotFoundError("missing.yml"))
def test_main_missing_config(mock_load):
    code = main(["-c", "missing.yml"])
    assert code == 2


@patch("cronwatch.cli.run_all", return_value=_ok_sr())
@patch("cronwatch.cli.load_config")
def test_main_dry_run_flag(mock_load, mock_run, tmp_path):
    cfg_file = tmp_path / "cw.yml"
    cfg_file.write_text("jobs: []\n")
    mock_load.return_value = MagicMock()

    main(["-c", str(cfg_file), "--dry-run"])

    _, kwargs = mock_run.call_args
    assert kwargs.get("dry_run") is True
