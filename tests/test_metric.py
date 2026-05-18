"""Tests for cronwatch.metric and cronwatch.metric_render."""
import json
from pathlib import Path

import pytest

from cronwatch.metric import (
    MetricSample,
    record_metric,
    list_metrics,
    summarize_metrics,
)
from cronwatch.metric_render import render_summary_table, render_sample_table


@pytest.fixture
def metric_file(tmp_path) -> Path:
    return tmp_path / "metrics.json"


def _sample(job="backup", ts="2024-01-01T00:00:00", dur=10.0, code=0):
    return MetricSample(job_name=job, timestamp=ts, duration_seconds=dur, exit_code=code)


def test_record_creates_file(metric_file):
    record_metric(metric_file, _sample())
    assert metric_file.exists()


def test_record_stores_fields(metric_file):
    record_metric(metric_file, _sample(dur=42.5, code=1))
    data = json.loads(metric_file.read_text())
    assert len(data) == 1
    assert data[0]["duration_seconds"] == 42.5
    assert data[0]["exit_code"] == 1


def test_multiple_records_accumulate(metric_file):
    for i in range(3):
        record_metric(metric_file, _sample(dur=float(i + 1)))
    assert len(list_metrics(metric_file)) == 3


def test_list_metrics_filter_by_job(metric_file):
    record_metric(metric_file, _sample(job="backup"))
    record_metric(metric_file, _sample(job="cleanup"))
    results = list_metrics(metric_file, job_name="backup")
    assert len(results) == 1
    assert results[0].job_name == "backup"


def test_list_metrics_empty_when_no_file(metric_file):
    assert list_metrics(metric_file) == []


def test_summarize_returns_none_when_no_data(metric_file):
    assert summarize_metrics(metric_file, "backup") is None


def test_summarize_correct_values(metric_file):
    for dur in [2.0, 4.0, 6.0, 8.0, 10.0]:
        record_metric(metric_file, _sample(dur=dur))
    s = summarize_metrics(metric_file, "backup")
    assert s is not None
    assert s.sample_count == 5
    assert s.min_duration == 2.0
    assert s.max_duration == 10.0
    assert s.avg_duration == 6.0


def test_sample_round_trip():
    s = _sample(dur=3.14, code=2)
    assert MetricSample.from_dict(s.to_dict()) == s


def test_render_summary_table_empty():
    out = render_summary_table([])
    assert "No metric" in out


def test_render_summary_table_includes_job_name(metric_file):
    for dur in [1.0, 2.0, 3.0]:
        record_metric(metric_file, _sample(job="myjob", dur=dur))
    s = summarize_metrics(metric_file, "myjob")
    out = render_summary_table([s])
    assert "myjob" in out
    assert "3" in out


def test_render_sample_table_empty():
    out = render_sample_table([])
    assert "No samples" in out


def test_render_sample_table_shows_duration(metric_file):
    record_metric(metric_file, _sample(dur=7.5))
    samples = list_metrics(metric_file)
    out = render_sample_table(samples)
    assert "7.500" in out
