"""Tests for cronwatch.forecast_render."""
from __future__ import annotations

from datetime import datetime, timezone

from cronwatch.forecast import ForecastResult
from cronwatch.forecast_render import render_forecast_table, _fmt_interval


def _result(
    name="backup",
    last_run=None,
    avg=None,
    next_exp=None,
    confidence="none",
) -> ForecastResult:
    return ForecastResult(
        job_name=name,
        last_run=last_run,
        avg_interval_seconds=avg,
        next_expected=next_exp,
        confidence=confidence,
    )


def test_render_empty_list() -> None:
    assert render_forecast_table([]) == "No forecast data available."


def test_render_includes_header() -> None:
    out = render_forecast_table([_result()])
    assert "JOB" in out
    assert "NEXT EXPECTED" in out
    assert "CONFIDENCE" in out


def test_render_includes_job_name() -> None:
    out = render_forecast_table([_result(name="nightly-sync")])
    assert "nightly-sync" in out


def test_render_confidence_none_shows_dash() -> None:
    out = render_forecast_table([_result(confidence="none")])
    assert "none" in out


def test_render_next_expected_formatted() -> None:
    dt = datetime(2024, 6, 1, 8, 30, 0, tzinfo=timezone.utc)
    r = _result(next_exp=dt, confidence="high", avg=3600)
    out = render_forecast_table([r])
    assert "2024-06-01 08:30:00" in out


def test_fmt_interval_minutes() -> None:
    assert _fmt_interval(300) == "5m"


def test_fmt_interval_hours() -> None:
    assert _fmt_interval(7200) == "2.0h"


def test_fmt_interval_days() -> None:
    assert _fmt_interval(86400) == "1.0d"


def test_fmt_interval_none() -> None:
    assert _fmt_interval(None) == "—"
