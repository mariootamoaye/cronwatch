"""Configuration dataclasses and YAML loader for cronwatch."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    max_duration: Optional[int] = None
    expected_interval: Optional[int] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    email: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25
    webhook_url: Optional[str] = None
    on_failure: bool = True
    on_timeout: bool = True
    on_slow: bool = False
    slow_threshold: Optional[int] = None


@dataclass
class RetentionConfig:
    max_age_days: Optional[int] = None
    max_entries: Optional[int] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    history_dir: str = ".cronwatch_history"


def _parse_job(raw: Dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        schedule=raw["schedule"],
        max_duration=raw.get("max_duration"),
        expected_interval=raw.get("expected_interval"),
        tags=[str(t) for t in raw.get("tags", [])],
    )


def _parse_alert(raw: Dict[str, Any]) -> AlertConfig:
    return AlertConfig(
        email=raw.get("email"),
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=int(raw.get("smtp_port", 25)),
        webhook_url=raw.get("webhook_url"),
        on_failure=raw.get("on_failure", True),
        on_timeout=raw.get("on_timeout", True),
        on_slow=raw.get("on_slow", False),
        slow_threshold=raw.get("slow_threshold"),
    )


def _parse_retention(raw: Dict[str, Any]) -> RetentionConfig:
    return RetentionConfig(
        max_age_days=raw.get("max_age_days"),
        max_entries=raw.get("max_entries"),
    )


def load_config(path: str) -> CronwatchConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as fh:
        data = yaml.safe_load(fh) or {}
    jobs = [_parse_job(j) for j in data.get("jobs", [])]
    alert = _parse_alert(data.get("alert", {}))
    retention = _parse_retention(data.get("retention", {}))
    history_dir = data.get("history_dir", ".cronwatch_history")
    return CronwatchConfig(jobs=jobs, alert=alert, retention=retention, history_dir=history_dir)
