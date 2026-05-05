"""Run all configured cron jobs and collect results."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from cronwatch.config import CronwatchConfig
from cronwatch.notifier import NotificationResult, dispatch
from cronwatch.runner import JobResult, run_job

logger = logging.getLogger(__name__)


@dataclass
class SchedulerResult:
    job_results: List[JobResult] = field(default_factory=list)
    notification_results: List[NotificationResult] = field(default_factory=list)

    @property
    def failed(self) -> List[JobResult]:
        return [
            r for r in self.job_results
            if r.exit_code != 0 or r.timed_out
        ]

    @property
    def all_ok(self) -> bool:
        return len(self.failed) == 0


def failed(sr: SchedulerResult) -> List[JobResult]:  # noqa: D103 — kept for backwards compat
    return sr.failed


def all_ok(sr: SchedulerResult) -> bool:  # noqa: D103 — kept for backwards compat
    return sr.all_ok


def run_all(config: CronwatchConfig) -> SchedulerResult:
    """Execute every job in *config* sequentially and dispatch alerts."""
    sr = SchedulerResult()

    for job_cfg in config.jobs:
        logger.info("Running job '%s': %s", job_cfg.name, job_cfg.command)
        job_result = run_job(job_cfg)
        sr.job_results.append(job_result)

        if config.alerts:
            notif = dispatch(job_result, config.alerts)
            sr.notification_results.append(notif)
            if not notif.nothing_sent and not notif.all_succeeded:
                logger.warning(
                    "Some notifications failed for job '%s': %s",
                    job_cfg.name,
                    notif.errors,
                )

    return sr
