"""Tests for cronwatch.runner module."""

import pytest
from unittest.mock import patch

from cronwatch.config import JobConfig
from cronwatch.runner import JobResult, run_job


def make_job(name="test-job", command="echo hello", max_duration=None):
    return JobConfig(name=name, command=command, schedule="* * * * *", max_duration=max_duration)


def test_successful_job():
    job = make_job(command="echo hello")
    result = run_job(job)
    assert result.success is True
    assert result.exit_code == 0
    assert result.timed_out is False
    assert result.stdout == "hello"
    assert result.job_name == "test-job"
    assert result.duration_seconds >= 0


def test_failed_job():
    job = make_job(command="exit 1")
    result = run_job(job)
    assert result.success is False
    assert result.exit_code == 1
    assert result.timed_out is False


def test_job_with_stderr():
    job = make_job(command="echo err >&2; exit 2")
    result = run_job(job)
    assert result.exit_code == 2
    assert "err" in result.stderr


def test_job_timeout():
    job = make_job(command="sleep 10", max_duration=0.1)
    result = run_job(job)
    assert result.timed_out is True
    assert result.success is False
    assert result.exit_code == -1


def test_job_result_fields():
    job = make_job(command="echo test")
    result = run_job(job)
    assert result.command == "echo test"
    assert result.started_at is not None
    assert result.finished_at is not None
    assert result.finished_at >= result.started_at


def test_job_result_success_property():
    result = JobResult(
        job_name="j",
        command="echo",
        exit_code=0,
        stdout="",
        stderr="",
        duration_seconds=0.1,
        started_at=__import__("datetime").datetime.utcnow(),
        finished_at=__import__("datetime").datetime.utcnow(),
        timed_out=False,
    )
    assert result.success is True
    result.timed_out = True
    assert result.success is False
