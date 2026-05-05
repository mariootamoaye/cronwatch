"""Configuration loader for cronwatch."""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str
    timeout: int = 3600  # seconds
    alert_on_failure: bool = True
    alert_on_timeout: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alerts: AlertConfig = field(default_factory=AlertConfig)
    log_file: str = "cronwatch.log"
    check_interval: int = 60


def load_config(path: str = "cronwatch.yml") -> CronwatchConfig:
    """Load configuration from a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raw = {}

    jobs = [
        JobConfig(
            name=j["name"],
            schedule=j["schedule"],
            timeout=j.get("timeout", 3600),
            alert_on_failure=j.get("alert_on_failure", True),
            alert_on_timeout=j.get("alert_on_timeout", True),
            tags=j.get("tags", []),
        )
        for j in raw.get("jobs", [])
    ]

    alert_raw = raw.get("alerts", {})
    alerts = AlertConfig(
        email=alert_raw.get("email"),
        webhook_url=alert_raw.get("webhook_url"),
        slack_channel=alert_raw.get("slack_channel"),
    )

    return CronwatchConfig(
        jobs=jobs,
        alerts=alerts,
        log_file=raw.get("log_file", "cronwatch.log"),
        check_interval=raw.get("check_interval", 60),
    )
