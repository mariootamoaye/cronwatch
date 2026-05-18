"""CLI commands for trend analysis."""
from __future__ import annotations

import argparse
from pathlib import Path

from cronwatch.config import load
from cronwatch.trend import analyze_trend


def _default_history_path() -> Path:
    return Path("cronwatch_history.json")


def cmd_trend_check(args: argparse.Namespace) -> int:
    history_path = Path(args.history) if args.history else _default_history_path()

    if args.config:
        cfg = load(Path(args.config))
        job_names = [j.name for j in cfg.jobs]
    else:
        job_names = args.jobs

    if not job_names:
        print("No jobs specified. Use --jobs or --config.")
        return 1

    any_degrading = False
    for job in job_names:
        result = analyze_trend(job, history_path, window_days=args.window)
        print(str(result))
        if result.is_degrading:
            any_degrading = True

    return 1 if (any_degrading and args.fail_on_degrading) else 0


def build_trend_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("trend", help="Analyse job success-rate trends")
    p.add_argument("--history", metavar="FILE", help="Path to history JSON file")
    p.add_argument("--config", metavar="FILE", help="cronwatch config file (loads all jobs)")
    p.add_argument("--jobs", nargs="+", metavar="JOB", default=[], help="Job names to analyse")
    p.add_argument("--window", type=int, default=7, metavar="DAYS", help="Window size in days (default: 7)")
    p.add_argument(
        "--fail-on-degrading",
        action="store_true",
        help="Exit with code 1 if any job is degrading",
    )
    p.set_defaults(func=cmd_trend_check)
    return p


def main() -> None:
    parser = argparse.ArgumentParser(description="cronwatch trend analysis")
    sub = parser.add_subparsers(dest="command")
    build_trend_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        raise SystemExit(0)
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
