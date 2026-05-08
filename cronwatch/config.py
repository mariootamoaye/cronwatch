"""Configuration loading for cronwatch."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    max_duration: Optional[int] = None  # seconds
    alert_on_failure: bool = True
    alert_on_timeout: bool = True


@dataclass
class AlertConfig:
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25
    webhook_url: Optional[str] = None


@dataclass
class RetentionConfig:
    max_age_days: Optional[int] = 90
    max_entries: Optional[int] = 1000


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    history_dir: str = "/var/lib/cronwatch"


def _parse_job(raw: dict) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        schedule=raw["schedule"],
        max_duration=raw.get("max_duration"),
        alert_on_failure=raw.get("alert_on_failure", True),
        alert_on_timeout=raw.get("alert_on_timeout", True),
    )


def _parse_alert(raw: dict) -> AlertConfig:
    return AlertConfig(
        email_to=raw.get("email_to"),
        email_from=raw.get("email_from"),
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=int(raw.get("smtp_port", 25)),
        webhook_url=raw.get("webhook_url"),
    )


def _parse_retention(raw: dict) -> RetentionConfig:
    return RetentionConfig(
        max_age_days=raw.get("max_age_days", 90),
        max_entries=raw.get("max_entries", 1000),
    )


def load_config(path: str) -> CronwatchConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path) as fh:
        raw = yaml.safe_load(fh) or {}
    jobs = [_parse_job(j) for j in raw.get("jobs", [])]
    alert = _parse_alert(raw.get("alert", {}))
    retention = _parse_retention(raw.get("retention", {}))
    history_dir = raw.get("history_dir", "/var/lib/cronwatch")
    return CronwatchConfig(jobs=jobs, alert=alert, retention=retention,
                           history_dir=history_dir)
