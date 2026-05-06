"""Tests for cronwatch.digest and cronwatch.digest_render."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cronwatch.digest import DigestStats, build_digest
from cronwatch.digest_render import render_body, render_subject


@pytest.fixture()
def history_file(tmp_path: Path) -> str:
    return str(tmp_path / "history.jsonl")


def _write(path: str, entries: list[dict]) -> None:
    Path(path).write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def _entry(
    job: str,
    hours_ago: float = 1,
    exit_code: int = 0,
    timed_out: bool = False,
    duration: float = 1.5,
) -> dict:
    ts = datetime.utcnow() - timedelta(hours=hours_ago)
    return {
        "job_name": job,
        "started_at": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "exit_code": exit_code,
        "duration": duration,
        "timed_out": timed_out,
        "stderr_snippet": "",
    }


def test_build_digest_empty(history_file: str) -> None:
    digest = build_digest(history_file, period_hours=24)
    assert digest.stats == []
    assert digest.all_healthy is True


def test_build_digest_all_ok(history_file: str) -> None:
    _write(history_file, [_entry("backup"), _entry("backup"), _entry("sync")])
    digest = build_digest(history_file, period_hours=24)
    assert len(digest.stats) == 2
    assert digest.all_healthy is True


def test_build_digest_with_failure(history_file: str) -> None:
    _write(history_file, [_entry("backup", exit_code=1), _entry("backup")])
    digest = build_digest(history_file, period_hours=24)
    stat = digest.stats[0]
    assert stat.failures == 1
    assert digest.all_healthy is False


def test_build_digest_with_timeout(history_file: str) -> None:
    _write(history_file, [_entry("sync", timed_out=True, exit_code=0)])
    digest = build_digest(history_file, period_hours=24)
    assert digest.stats[0].timeouts == 1
    assert digest.all_healthy is False


def test_success_rate(history_file: str) -> None:
    entries = [_entry("j", exit_code=0)] * 3 + [_entry("j", exit_code=1)]
    _write(history_file, entries)
    digest = build_digest(history_file, period_hours=24)
    assert digest.stats[0].success_rate == 75.0


def test_old_entries_excluded(history_file: str) -> None:
    _write(history_file, [_entry("old_job", hours_ago=48)])
    digest = build_digest(history_file, period_hours=24)
    assert digest.stats == []


def test_render_subject_ok(history_file: str) -> None:
    digest = build_digest(history_file, period_hours=24)
    subj = render_subject(digest)
    assert "OK" in subj
    assert "24h digest" in subj


def test_render_subject_issues(history_file: str) -> None:
    _write(history_file, [_entry("job", exit_code=1)])
    digest = build_digest(history_file, period_hours=24)
    subj = render_subject(digest)
    assert "ISSUES DETECTED" in subj


def test_render_body_contains_job_name(history_file: str) -> None:
    _write(history_file, [_entry("my_job")])
    digest = build_digest(history_file, period_hours=24)
    body = render_body(digest)
    assert "my_job" in body
    assert "Jobs healthy" in body


def test_render_body_no_entries(history_file: str) -> None:
    digest = build_digest(history_file, period_hours=12)
    body = render_body(digest)
    assert "No jobs recorded" in body
