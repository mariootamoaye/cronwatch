"""Configuration models and loader for cronwatch."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class JobConfig:
    name: str
    command: str
    schedule: str
    max_duration: Optional[int] = None  # seconds
    timeout: Optional[int] = None  # seconds


@dataclass
class AlertConfig:
    email: Optional[str] = None
    on_failure: bool = True
    on_timeout: bool = True
    on_slow: bool = False
    slow_threshold: Optional[int] = None  # seconds


@dataclass
class RetentionConfig:
    max_age_days: Optional[int] = None
    max_entries: Optional[int] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    history_dir: Path = field(default_factory=lambda: Path("~/.cronwatch/history").expanduser())
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_from: str = "cronwatch@localhost"


def _parse_job(raw: Dict) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        schedule=raw["schedule"],
        max_duration=raw.get("max_duration"),
        timeout=raw.get("timeout"),
    )


def _parse_alert(raw: Dict) -> AlertConfig:
    return AlertConfig(
        email=raw.get("email"),
        on_failure=raw.get("on_failure", True),
        on_timeout=raw.get("on_timeout", True),
        on_slow=raw.get("on_slow", False),
        slow_threshold=raw.get("slow_threshold"),
    )


def _parse_retention(raw: Dict) -> RetentionConfig:
    return RetentionConfig(
        max_age_days=raw.get("max_age_days"),
        max_entries=raw.get("max_entries"),
    )


def load_config(path: Path) -> CronwatchConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as fh:
        raw = yaml.safe_load(fh) or {}

    jobs = [_parse_job(j) for j in raw.get("jobs", [])]
    alert = _parse_alert(raw.get("alert", {}))
    retention = _parse_retention(raw.get("retention", {}))
    history_dir = Path(raw.get("history_dir", "~/.cronwatch/history")).expanduser()

    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        retention=retention,
        history_dir=history_dir,
        smtp_host=raw.get("smtp_host", "localhost"),
        smtp_port=int(raw.get("smtp_port", 25)),
        smtp_from=raw.get("smtp_from", "cronwatch@localhost"),
    )
