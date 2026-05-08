"""Tests for cronwatch.status and cronwatch.status_render."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.status import JobStatus, StatusBoard, _consecutive_failures, build_status_board
from cronwatch.status_render import render_status_board


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(offset_seconds: int = 0) -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _write_entry(history_dir: Path, job_name: str, exit_code: int, offset: int = 0):
    job_dir = history_dir / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime(2024, 6, 1, 12, offset, 0, tzinfo=timezone.utc)
    entry = {
        "timestamp": ts.isoformat(),
        "exit_code": exit_code,
        "duration": 1.5 + offset,
        "stdout": "",
        "stderr": "",
    }
    fname = job_dir / f"{ts.strftime('%Y%m%dT%H%M%S')}.json"
    fname.write_text(json.dumps(entry))


@pytest.fixture()
def history_dir(tmp_path):
    return tmp_path / "history"


# ---------------------------------------------------------------------------
# JobStatus unit tests
# ---------------------------------------------------------------------------

def test_job_status_ok():
    s = JobStatus("backup", _ts(), 0, 2.0, 0)
    assert s.ok
    assert not s.never_run


def test_job_status_fail():
    s = JobStatus("backup", _ts(), 1, 2.0, 3)
    assert not s.ok


def test_job_status_never_run():
    s = JobStatus("backup", None, None, None, 0)
    assert s.never_run


# ---------------------------------------------------------------------------
# StatusBoard
# ---------------------------------------------------------------------------

def test_status_board_all_ok():
    jobs = [JobStatus("a", _ts(), 0, 1.0, 0), JobStatus("b", _ts(), 0, 2.0, 0)]
    board = StatusBoard(jobs)
    assert board.all_ok
    assert board.failing == []


def test_status_board_with_failure():
    jobs = [JobStatus("a", _ts(), 0, 1.0, 0), JobStatus("b", _ts(), 1, 2.0, 2)]
    board = StatusBoard(jobs)
    assert not board.all_ok
    assert len(board.failing) == 1
    assert board.failing[0].job_name == "b"


# ---------------------------------------------------------------------------
# build_status_board
# ---------------------------------------------------------------------------

def test_build_status_board_no_history(history_dir):
    board = build_status_board(str(history_dir), ["nightly"])
    assert len(board.jobs) == 1
    assert board.jobs[0].never_run


def test_build_status_board_with_history(history_dir):
    _write_entry(history_dir, "nightly", 0, offset=0)
    _write_entry(history_dir, "nightly", 1, offset=1)
    board = build_status_board(str(history_dir), ["nightly"])
    assert not board.jobs[0].ok
    assert board.jobs[0].consecutive_failures == 1


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def test_render_includes_job_name():
    board = StatusBoard([JobStatus("my-job", _ts(), 0, 5.0, 0)])
    text = render_status_board(board)
    assert "my-job" in text
    assert "OK" in text


def test_render_overall_failing():
    board = StatusBoard([JobStatus("bad-job", _ts(), 2, 1.0, 3)])
    text = render_status_board(board)
    assert "failing" in text
