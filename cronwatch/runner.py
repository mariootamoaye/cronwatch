"""Job runner module for cronwatch."""

import subprocess
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from cronwatch.config import JobConfig

logger = logging.getLogger(__name__)


@dataclass
class JobResult:
    """Result of a cron job execution."""

    job_name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: datetime
    finished_at: datetime
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    @property
    def exceeded_max_duration(self) -> Optional[bool]:
        return None  # Evaluated externally against JobConfig.max_duration


def run_job(job: JobConfig) -> JobResult:
    """Execute a cron job and return the result."""
    logger.info("Starting job '%s': %s", job.name, job.command)
    started_at = datetime.utcnow()
    start_time = time.monotonic()
    timed_out = False

    try:
        proc = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=job.max_duration if job.max_duration else None,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = -1
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        logger.warning("Job '%s' timed out after %s seconds", job.name, job.max_duration)

    duration = time.monotonic() - start_time
    finished_at = datetime.utcnow()

    result = JobResult(
        job_name=job.name,
        command=job.command,
        exit_code=exit_code,
        stdout=stdout.strip() if stdout else "",
        stderr=stderr.strip() if stderr else "",
        duration_seconds=round(duration, 3),
        started_at=started_at,
        finished_at=finished_at,
        timed_out=timed_out,
    )

    logger.info(
        "Job '%s' finished in %.3fs with exit code %d",
        job.name,
        result.duration_seconds,
        result.exit_code,
    )
    return result
