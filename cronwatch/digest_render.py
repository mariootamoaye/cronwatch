"""Render a Digest into plain-text and subject line for email delivery."""
from __future__ import annotations

from cronwatch.digest import Digest

_SEP = "-" * 60


def render_subject(digest: Digest) -> str:
    status = "OK" if digest.all_healthy else "ISSUES DETECTED"
    return (
        f"[cronwatch] {digest.period_hours}h digest — {status} "
        f"({digest.generated_at.strftime('%Y-%m-%d %H:%M')} UTC)"
    )


def render_body(digest: Digest) -> str:
    lines: list[str] = [
        f"Cronwatch digest — last {digest.period_hours} hours",
        f"Generated: {digest.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        _SEP,
    ]

    if not digest.stats:
        lines.append("No jobs recorded in this period.")
        return "\n".join(lines)

    header = f"{'Job':<30} {'Runs':>5} {'Failures':>9} {'Timeouts':>9} {'SuccessRate':>12} {'AvgDur(s)':>10}"
    lines.append(header)
    lines.append(_SEP)

    for s in digest.stats:
        last = s.last_run.strftime("%Y-%m-%d %H:%M") if s.last_run else "n/a"
        row = (
            f"{s.job_name:<30} {s.total_runs:>5} {s.failures:>9} "
            f"{s.timeouts:>9} {s.success_rate:>11}% {s.avg_duration:>10.2f}"
        )
        lines.append(row)

    lines.append(_SEP)
    ok = sum(1 for s in digest.stats if s.failures == 0 and s.timeouts == 0)
    lines.append(f"Jobs healthy: {ok}/{len(digest.stats)}")
    return "\n".join(lines)
