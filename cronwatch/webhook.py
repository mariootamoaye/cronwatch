"""Webhook alert delivery for cronwatch."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

from cronwatch.runner import JobResult
from cronwatch.config import AlertConfig


@dataclass(frozen=True)
class WebhookResult:
    job_name: str
    url: str
    status_code: Optional[int]
    success: bool
    error: Optional[str] = None


def _build_payload(job_name: str, result: JobResult) -> dict:
    return {
        "job": job_name,
        "exit_code": result.exit_code,
        "duration_seconds": round(result.duration, 3),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
    }


def send_webhook(job_name: str, result: JobResult, alert_cfg: AlertConfig) -> WebhookResult:
    """POST a JSON payload to the configured webhook URL."""
    url = alert_cfg.webhook_url
    if not url:
        return WebhookResult(job_name=job_name, url="", status_code=None,
                             success=False, error="No webhook URL configured")

    payload = _build_payload(job_name, result)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return WebhookResult(
                job_name=job_name,
                url=url,
                status_code=resp.status,
                success=200 <= resp.status < 300,
            )
    except urllib.error.HTTPError as exc:
        return WebhookResult(job_name=job_name, url=url, status_code=exc.code,
                             success=False, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return WebhookResult(job_name=job_name, url=url, status_code=None,
                             success=False, error=str(exc))
