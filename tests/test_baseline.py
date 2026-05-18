"""Tests for cronwatch.baseline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.baseline import (
    BaselineStats,
    check_baseline,
    compute_stats,
    record_duration,
)


@pytest.fixture()
def baseline_file(tmp_path: Path) -> Path:
    return tmp_path / "baseline.json"


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh)


# ---------------------------------------------------------------------------
# BaselineStats
# ---------------------------------------------------------------------------

def test_upper_bound_is_mean_plus_two_stddev():
    s = BaselineStats(job_name="j", sample_count=10, mean_seconds=30.0, stddev_seconds=5.0)
    assert s.upper_bound == pytest.approx(40.0)


def test_is_anomalous_true_when_above_upper_bound():
    s = BaselineStats(job_name="j", sample_count=10, mean_seconds=30.0, stddev_seconds=5.0)
    assert s.is_anomalous(41.0) is True


def test_is_anomalous_false_when_within_bound():
    s = BaselineStats(job_name="j", sample_count=10, mean_seconds=30.0, stddev_seconds=5.0)
    assert s.is_anomalous(39.0) is False


def test_is_anomalous_false_when_fewer_than_3_samples():
    s = BaselineStats(job_name="j", sample_count=2, mean_seconds=30.0, stddev_seconds=5.0)
    assert s.is_anomalous(9999.0) is False


# ---------------------------------------------------------------------------
# record_duration
# ---------------------------------------------------------------------------

def test_record_duration_creates_file(baseline_file: Path):
    record_duration("backup", 10.0, baseline_file)
    assert baseline_file.exists()


def test_record_duration_appends_samples(baseline_file: Path):
    record_duration("backup", 10.0, baseline_file)
    record_duration("backup", 12.0, baseline_file)
    data = json.loads(baseline_file.read_text())
    assert data["backup"] == [10.0, 12.0]


def test_record_duration_caps_at_max_samples(baseline_file: Path):
    for i in range(60):
        record_duration("j", float(i), baseline_file, max_samples=50)
    data = json.loads(baseline_file.read_text())
    assert len(data["j"]) == 50
    assert data["j"][0] == 10.0  # oldest 10 entries dropped


# ---------------------------------------------------------------------------
# compute_stats
# ---------------------------------------------------------------------------

def test_compute_stats_none_when_no_data(baseline_file: Path):
    assert compute_stats("missing", baseline_file) is None


def test_compute_stats_none_with_single_sample(baseline_file: Path):
    _write(baseline_file, {"j": [5.0]})
    assert compute_stats("j", baseline_file) is None


def test_compute_stats_returns_values(baseline_file: Path):
    _write(baseline_file, {"j": [10.0, 20.0, 30.0]})
    stats = compute_stats("j", baseline_file)
    assert stats is not None
    assert stats.sample_count == 3
    assert stats.mean_seconds == pytest.approx(20.0)
    assert stats.stddev_seconds > 0


# ---------------------------------------------------------------------------
# check_baseline
# ---------------------------------------------------------------------------

def test_check_baseline_ok_within_bounds(baseline_file: Path):
    _write(baseline_file, {"j": [10.0, 10.0, 10.0, 10.0, 10.0]})
    result = check_baseline("j", 10.5, baseline_file)
    assert result.ok is True
    assert result.anomalous is False


def test_check_baseline_anomalous_when_far_above_mean(baseline_file: Path):
    _write(baseline_file, {"j": [10.0, 10.0, 10.0, 10.0, 10.0]})
    result = check_baseline("j", 9999.0, baseline_file)
    assert result.anomalous is True
    assert result.ok is False


def test_check_baseline_not_anomalous_with_no_history(baseline_file: Path):
    result = check_baseline("new_job", 999.0, baseline_file)
    assert result.anomalous is False
    assert result.stats is None
