"""Dispatch notifications (email, webhook) for job results."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cronwatch.alerts import should_alert, send_email_alert
from cronwatch.config import AlertConfig
from cronwatch.mute import is_muted, _DEFAULT_PATH as _MUTE_PATH
from cronwatch.runner import JobResult
from cronwatch.webhook import send_webhook


@dataclass
class NotificationResult:
    job_name: str
    email_sent: bool = False
    webhook_sent: bool = False
    muted: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return not self.errors

    @property
    def nothing_sent(self) -> bool:
        return not self.email_sent and not self.webhook_sent

    def __str__(self) -> str:
        """Return a human-readable summary of the notification outcome."""
        if self.muted:
            return f"[{self.job_name}] muted – no notifications sent"
        parts = []
        if self.email_sent:
            parts.append("email")
        if self.webhook_sent:
            parts.append("webhook")
        sent = ", ".join(parts) if parts else "none"
        error_summary = f"; errors: {'; '.join(self.errors)}" if self.errors else ""
        return f"[{self.job_name}] sent={sent}{error_summary}"


def dispatch(
    result: JobResult,
    alert_cfg: AlertConfig,
    mute_path: Optional[Path] = None,
) -> NotificationResult:
    """Send alerts for *result* unless the job is muted or no alert is needed."""
    mute_path = mute_path or _MUTE_PATH
    nr = NotificationResult(job_name=result.job.name)

    if is_muted(result.job.name, path=mute_path):
        nr.muted = True
        return nr

    if not should_alert(result, alert_cfg):
        return nr

    if alert_cfg.email:
        outcome = send_email_alert(result, alert_cfg)
        if outcome.success:
            nr.email_sent = True
        else:
            nr.errors.append(f"email: {outcome.error}")

    if alert_cfg.webhook_url:
        outcome = send_webhook(result, alert_cfg)
        if outcome.success:
            nr.webhook_sent = True
        else:
            nr.errors.append(f"webhook: {outcome.error}")

    return nr
