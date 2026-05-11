"""CLI helpers for inspecting and managing alert rate-limit state."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from cronwatch.ratelimit import _load_raw, clear_rate_limit


def _default_rl_path() -> Path:
    return Path.home() / ".cronwatch" / "ratelimit.json"


def cmd_rl_list(args: argparse.Namespace) -> int:
    """List all jobs that are currently in a rate-limit cooldown."""
    path = Path(args.state_file) if args.state_file else _default_rl_path()
    data = _load_raw(path)
    if not data:
        print("No rate-limit records found.")
        return 0

    now = time.time()
    cooldown = args.cooldown
    rows = []
    for job_name, ts in sorted(data.items()):
        elapsed = now - ts
        remaining = cooldown - elapsed
        status = f"cooling ({int(remaining)}s left)" if remaining > 0 else "expired"
        rows.append((job_name, status))

    width = max(len(r[0]) for r in rows)
    print(f"{'JOB':<{width}}  STATUS")
    print("-" * (width + 20))
    for job_name, status in rows:
        print(f"{job_name:<{width}}  {status}")
    return 0


def cmd_rl_clear(args: argparse.Namespace) -> int:
    """Remove the rate-limit record for a specific job."""
    path = Path(args.state_file) if args.state_file else _default_rl_path()
    removed = clear_rate_limit(path, args.job)
    if removed:
        print(f"Rate-limit record cleared for '{args.job}'.")
    else:
        print(f"No rate-limit record found for '{args.job}'.")
    return 0


def build_ratelimit_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'ratelimit' sub-commands onto *subparsers*."""
    rl = subparsers.add_parser("ratelimit", help="Manage alert rate-limit state")
    rl_sub = rl.add_subparsers(dest="rl_cmd", required=True)

    # shared option
    _shared = argparse.ArgumentParser(add_help=False)
    _shared.add_argument("--state-file", default=None, metavar="PATH",
                         help="Path to ratelimit state file")
    _shared.add_argument("--cooldown", type=int, default=300, metavar="SECS",
                         help="Cooldown window in seconds (default: 300)")

    # list
    rl_sub.add_parser("list", parents=[_shared],
                      help="Show current rate-limit records")

    # clear
    p_clear = rl_sub.add_parser("clear", parents=[_shared],
                                help="Clear rate-limit record for a job")
    p_clear.add_argument("job", help="Job name to clear")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cronwatch-ratelimit")
    subs = parser.add_subparsers(dest="cmd", required=True)
    build_ratelimit_parser(subs)
    args = parser.parse_args(argv)
    if args.rl_cmd == "list":
        return cmd_rl_list(args)
    if args.rl_cmd == "clear":
        return cmd_rl_clear(args)
    return 1
