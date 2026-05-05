"""Notification dispatcher: routes alerts to configured channels."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from cronwatch.alerts import send_email_alert, should_alert
from cronwatch.config import AlertConfig
from cronwatch.runner import JobResult

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    job_name: str
    channels_attempted: List[str] = field(default_factory=list)
    channels_succeeded: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return len(self.errors) == 0 and len(self.channels_attempted) > 0

    @property
    def nothing_sent(self) -> bool:
        return len(self.channels_attempted) == 0


def dispatch(job_result: JobResult, alert_cfg: AlertConfig) -> NotificationResult:
    """Dispatch notifications for a job result to all configured channels."""
    result = NotificationResult(job_name=job_result.job_name)

    if not should_alert(job_result, alert_cfg):
        logger.debug("No alert needed for job '%s'", job_result.job_name)
        return result

    if alert_cfg.email:
        result.channels_attempted.append("email")
        try:
            send_email_alert(job_result, alert_cfg)
            result.channels_succeeded.append("email")
            logger.info("Email alert sent for job '%s'", job_result.job_name)
        except Exception as exc:  # noqa: BLE001
            msg = f"email: {exc}"
            result.errors.append(msg)
            logger.error("Failed to send email alert for job '%s': %s", job_result.job_name, exc)

    return result
