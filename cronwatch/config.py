"""Configuration loading for cronwatch.

This file extends the existing config with `depends_on` support on JobConfig.
Only the JobConfig dataclass and _parse_job helper are shown changed;
all other symbols remain as before.
"""
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
    max_duration: Optional[int] = None          # seconds
    alert_on_failure: bool = True
    alert_on_timeout: bool = True
    tags: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # NEW


@dataclass
class AlertConfig:
    email: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25
    from_address: str = "cronwatch@localhost"
    webhook_url: Optional[str] = None


@dataclass
class RetentionConfig:
    max_age_days: Optional[int] = None
    max_entries: Optional[int] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig]
    alerts: AlertConfig
    retention: RetentionConfig
    history_dir: str = ".cronwatch/history"

    @classmethod
    def load(cls, path: str) -> "CronwatchConfig":
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as fh:
            raw: Dict[str, Any] = yaml.safe_load(fh) or {}
        return _parse_config(raw)


def _parse_job(raw: Dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        schedule=raw.get("schedule", ""),
        max_duration=raw.get("max_duration"),
        alert_on_failure=raw.get("alert_on_failure", True),
        alert_on_timeout=raw.get("alert_on_timeout", True),
        tags=raw.get("tags") or [],
        depends_on=raw.get("depends_on") or [],  # NEW
    )


def _parse_alerts(raw: Optional[Dict[str, Any]]) -> AlertConfig:
    if not raw:
        return AlertConfig()
    return AlertConfig(
        email=raw.get("email"),
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=int(raw.get("smtp_port", 25)),
        from_address=raw.get("from_address", "cronwatch@localhost"),
        webhook_url=raw.get("webhook_url"),
    )


def _parse_retention(raw: Optional[Dict[str, Any]]) -> RetentionConfig:
    if not raw:
        return RetentionConfig()
    return RetentionConfig(
        max_age_days=raw.get("max_age_days"),
        max_entries=raw.get("max_entries"),
    )


def _parse_config(raw: Dict[str, Any]) -> CronwatchConfig:
    jobs = [_parse_job(j) for j in raw.get("jobs", [])]
    alerts = _parse_alerts(raw.get("alerts"))
    retention = _parse_retention(raw.get("retention"))
    history_dir = raw.get("history_dir", ".cronwatch/history")
    return CronwatchConfig(
        jobs=jobs,
        alerts=alerts,
        retention=retention,
        history_dir=history_dir,
    )
