"""Configuration models and loader for cronwatch."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    timeout: Optional[int] = None
    max_duration: Optional[int] = None


@dataclass
class AlertConfig:
    email: Optional[str] = None
    on_failure: bool = True
    on_timeout: bool = True
    on_slow: bool = False


@dataclass
class RetentionConfig:
    max_age_days: Optional[int] = None
    max_entries: Optional[int] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    history_path: str = "~/.cronwatch/history.json"
    retention: RetentionConfig = field(default_factory=RetentionConfig)


def load_config(path: str) -> CronwatchConfig:
    config_path = pathlib.Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with config_path.open() as fh:
        raw = yaml.safe_load(fh) or {}

    jobs = [
        JobConfig(
            name=j["name"],
            command=j["command"],
            schedule=j["schedule"],
            timeout=j.get("timeout"),
            max_duration=j.get("max_duration"),
        )
        for j in raw.get("jobs", [])
    ]

    alert_raw = raw.get("alert", {})
    alert = AlertConfig(
        email=alert_raw.get("email"),
        on_failure=alert_raw.get("on_failure", True),
        on_timeout=alert_raw.get("on_timeout", True),
        on_slow=alert_raw.get("on_slow", False),
    )

    retention_raw = raw.get("retention", {})
    retention = RetentionConfig(
        max_age_days=retention_raw.get("max_age_days"),
        max_entries=retention_raw.get("max_entries"),
    )

    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        history_path=raw.get("history_path", "~/.cronwatch/history.json"),
        retention=retention,
    )
