"""CLI helpers for threshold checks."""
from __future__ import annotations

import argparse
import os
import sys

from cronwatch.config import load
from cronwatch.threshold import check_threshold, ThresholdReport


def _default_history_path(job_name: str, base_dir: str = "~/.cronwatch/history") -> str:
    safe = job_name.replace(" ", "_")
    return os.path.expanduser(os.path.join(base_dir, f"{safe}.json"))


def cmd_threshold_check(args: argparse.Namespace) -> int:
    """Run threshold checks for all configured jobs and print a report."""
    try:
        cfg = load(args.config)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    report = ThresholdReport()

    for job in cfg.jobs:
        thresholds = getattr(job, "thresholds", None) or {}
        for metric, limit in thresholds.items():
            history_path = _default_history_path(job.name)
            result = check_threshold(
                job_name=job.name,
                metric=metric,
                limit=float(limit),
                history_path=history_path,
                window=args.window,
            )
            report.results.append(result)
            print(result)

    if not report.results:
        print("No threshold rules configured.")
        return 0

    if report.all_ok:
        print("\nAll thresholds OK.")
        return 0

    print(f"\n{len(report.breached)} threshold(s) breached.")
    return 1


def build_threshold_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("threshold", help="Check metric thresholds for configured jobs")
    p.add_argument("-c", "--config", default="cronwatch/cronwatch.yml", help="Config file path")
    p.add_argument("-w", "--window", type=int, default=10, metavar="N",
                   help="Number of recent history entries to evaluate (default: 10)")
    p.set_defaults(func=cmd_threshold_check)
    return p


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="cronwatch threshold checker")
    sub = parser.add_subparsers(dest="command")
    build_threshold_parser(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
