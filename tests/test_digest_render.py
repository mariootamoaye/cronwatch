"""Unit tests focused on digest_render edge cases."""
from __future__ import annotations

from datetime import datetime

from cronwatch.digest import Digest, DigestStats
from cronwatch.digest_render import render_body, render_subject


def _digest(stats: list[DigestStats], period: int = 24) -> Digest:
    return Digest(
        period_hours=period,
        generated_at=datetime(2024, 6, 1, 12, 0, 0),
        stats=stats,
    )


def test_subject_includes_period() -> None:
    d = _digest([], period=12)
    assert "12h digest" in render_subject(d)


def test_subject_timestamp_format() -> None:
    d = _digest([])
    assert "2024-06-01 12:00" in render_subject(d)


def test_body_header_row() -> None:
    d = _digest([DigestStats(job_name="nightly", total_runs=5)])
    body = render_body(d)
    assert "Job" in body
    assert "SuccessRate" in body


def test_body_healthy_count() -> None:
    stats = [
        DigestStats("a", total_runs=2, failures=0, timeouts=0),
        DigestStats("b", total_runs=3, failures=1, timeouts=0),
    ]
    body = render_body(_digest(stats))
    assert "Jobs healthy: 1/2" in body


def test_body_avg_duration_displayed() -> None:
    stats = [DigestStats("job", total_runs=1, avg_duration=3.75)]
    body = render_body(_digest(stats))
    assert "3.75" in body


def test_success_rate_100_when_no_runs() -> None:
    s = DigestStats(job_name="empty")
    assert s.success_rate == 100.0
