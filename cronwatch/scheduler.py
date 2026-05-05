"""Scheduler: reads config and dispatches cron jobs, collecting results."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from cronwatch.alerts import send_email_alert, should_alert
from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.runner import JobResult, run_job

logger = logging.getLogger(__name__)


@dataclass
class SchedulerResult:
    """Aggregated outcome of running all configured jobs."""

    results: List[JobResult] = field(default_factory=list)

    @property
    def failed(self) -> List[JobResult]:
        return [r for r in self.results if not r.success or r.exceeded_max_duration]

    @property
    def all_ok(self) -> bool:
        return len(self.failed) == 0


def run_all(config: CronwatchConfig, *, dry_run: bool = False) -> SchedulerResult:
    """Run every job defined in *config* and send alerts as needed.

    Parameters
    ----------
    config:
        Parsed :class:`CronwatchConfig` instance.
    dry_run:
        When *True* jobs are executed but alerts are **not** sent.
    """
    scheduler_result = SchedulerResult()

    for job_cfg in config.jobs:
        logger.info("Running job '%s': %s", job_cfg.name, job_cfg.command)
        result = run_job(job_cfg)
        scheduler_result.results.append(result)

        if should_alert(result, config.alerts):
            if dry_run:
                logger.info(
                    "[dry-run] Would send alert for job '%s'", job_cfg.name
                )
            else:
                send_email_alert(result, config.alerts)
        else:
            logger.debug("No alert needed for job '%s'", job_cfg.name)

    return scheduler_result
