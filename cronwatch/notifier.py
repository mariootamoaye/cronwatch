"""Dispatch alerts (email + webhook) for a job result."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.alerts import should_alert, send_email_alert
from cronwatch.webhook import send_webhook, WebhookResult
from cronwatch.runner import JobResult
from cronwatch.config import AlertConfig


@dataclass(frozen=True)
class NotificationResult:
    job_name: str
    email_sent: bool
    webhook_sent: bool
    webhook_result: Optional[WebhookResult] = None
    error: Optional[str] = None

    def all_succeeded(self) -> bool:
        return self.email_sent or self.webhook_sent

    def nothing_sent(self) -> bool:
        return not self.email_sent and not self.webhook_sent


def dispatch(job_name: str, result: JobResult, alert_cfg: AlertConfig) -> NotificationResult:
    """Send all configured alerts for a job result."""
    if not should_alert(result, alert_cfg):
        return NotificationResult(job_name=job_name, email_sent=False, webhook_sent=False)

    email_sent = False
    webhook_result: Optional[WebhookResult] = None
    error: Optional[str] = None

    if alert_cfg.email_to:
        try:
            send_email_alert(job_name, result, alert_cfg)
            email_sent = True
        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    if alert_cfg.webhook_url:
        webhook_result = send_webhook(job_name, result, alert_cfg)

    return NotificationResult(
        job_name=job_name,
        email_sent=email_sent,
        webhook_result=webhook_result,
        webhook_sent=webhook_result is not None and webhook_result.success,
        error=error,
    )
