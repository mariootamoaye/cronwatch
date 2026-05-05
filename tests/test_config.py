"""Tests for cronwatch config loader."""

import os
import pytest
import tempfile
import yaml

from cronwatch.config import load_config, CronwatchConfig, JobConfig, AlertConfig


MINIMAL_CONFIG = {
    "jobs": [
        {"name": "test-job", "schedule": "* * * * *"}
    ]
}

FULL_CONFIG = {
    "log_file": "test.log",
    "check_interval": 30,
    "alerts": {
        "email": "test@example.com",
        "webhook_url": "https://hooks.example.com/abc",
        "slack_channel": "#alerts",
    },
    "jobs": [
        {
            "name": "backup",
            "schedule": "0 2 * * *",
            "timeout": 900,
            "alert_on_failure": True,
            "alert_on_timeout": False,
            "tags": ["backup", "nightly"],
        }
    ],
}


@pytest.fixture
def config_file(tmp_path):
    def _write(data):
        path = tmp_path / "cronwatch.yml"
        with open(path, "w") as f:
            yaml.dump(data, f)
        return str(path)
    return _write


def test_load_minimal_config(config_file):
    path = config_file(MINIMAL_CONFIG)
    config = load_config(path)
    assert isinstance(config, CronwatchConfig)
    assert len(config.jobs) == 1
    assert config.jobs[0].name == "test-job"
    assert config.jobs[0].timeout == 3600
    assert config.jobs[0].alert_on_failure is True


def test_load_full_config(config_file):
    path = config_file(FULL_CONFIG)
    config = load_config(path)
    assert config.log_file == "test.log"
    assert config.check_interval == 30
    assert config.alerts.email == "test@example.com"
    assert config.alerts.webhook_url == "https://hooks.example.com/abc"
    assert config.alerts.slack_channel == "#alerts"
    job = config.jobs[0]
    assert job.name == "backup"
    assert job.timeout == 900
    assert job.alert_on_timeout is False
    assert "nightly" in job.tags


def test_missing_config_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/cronwatch.yml")


def test_empty_config_file(tmp_path):
    path = tmp_path / "cronwatch.yml"
    path.write_text("")
    config = load_config(str(path))
    assert config.jobs == []
    assert config.log_file == "cronwatch.log"
    assert config.check_interval == 60


def test_defaults_applied(config_file):
    path = config_file({"jobs": [{"name": "j", "schedule": "* * * * *"}]})
    config = load_config(path)
    job = config.jobs[0]
    assert job.timeout == 3600
    assert job.alert_on_failure is True
    assert job.alert_on_timeout is True
    assert job.tags == []
