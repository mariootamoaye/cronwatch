"""Alert dispatching for cronwatch."""

import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from cronwatch.config import AlertConfig
from cronwatch.runner import JobResult

logger = logging.getLogger(__name__)


def _build_subject(result: JobResult, max_duration: Optional[float]) -> str:
    if result.timed_out:
        return f"[cronwatch] TIMEOUT: {result.job_name}"
    if not result.success:
        return f"[cronwatch] FAILED: {result.job_name} (exit {result.exit_code})"
    if max_duration and result.duration_seconds > max_duration:
        return f"[cronwatch] SLOW: {result.job_name} ({result.duration_seconds:.1f}s)"
    return f"[cronwatch] OK: {result.job_name}"


def _build_body(result: JobResult) -> str:
    lines = [
        f"Job:      {result.job_name}",
        f"Command:  {result.command}",
        f"Started:  {result.started_at.isoformat()}Z",
        f"Duration: {result.duration_seconds:.3f}s",
        f"Exit code: {result.exit_code}",
        f"Timed out: {result.timed_out}",
    ]
    if result.stdout:
        lines += ["", "--- stdout ---", result.stdout]
    if result.stderr:
        lines += ["", "--- stderr ---", result.stderr]
    return "\n".join(lines)


def should_alert(result: JobResult, max_duration: Optional[float]) -> bool:
    """Return True if an alert should be sent for this result."""
    if not result.success:
        return True
    if max_duration and result.duration_seconds > max_duration:
        return True
    return False


def send_email_alert(
    result: JobResult,
    alert_cfg: AlertConfig,
    max_duration: Optional[float] = None,
) -> None:
    """Send an email alert for a job result."""
    subject = _build_subject(result, max_duration)
    body = _build_body(result)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = alert_cfg.from_email
    msg["To"] = ", ".join(alert_cfg.to_emails)
    msg.set_content(body)

    host = alert_cfg.smtp_host
    port = alert_cfg.smtp_port
    logger.info("Sending alert email to %s via %s:%d", alert_cfg.to_emails, host, port)

    with smtplib.SMTP(host, port) as smtp:
        if alert_cfg.smtp_username and alert_cfg.smtp_password:
            smtp.login(alert_cfg.smtp_username, alert_cfg.smtp_password)
        smtp.send_message(msg)

    logger.info("Alert sent: %s", subject)
