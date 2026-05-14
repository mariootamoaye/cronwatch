"""CLI sub-commands for inspecting job dependency status."""
from __future__ import annotations

import argparse
import sys
from typing import List

from cronwatch.config import CronwatchConfig
from cronwatch.dependency import check_all_dependencies


def _build_dep_map(cfg: CronwatchConfig) -> dict:
    return {
        job.name: list(job.depends_on)
        for job in cfg.jobs
        if job.depends_on
    }


def cmd_dep_check(args: argparse.Namespace) -> int:
    """Print dependency status for all jobs and exit non-zero if any are blocked."""
    cfg = CronwatchConfig.load(args.config)
    dep_map = _build_dep_map(cfg)

    if not dep_map:
        print("No job dependencies configured.")
        return 0

    report = check_all_dependencies(dep_map, cfg.history_dir)

    for result in report.results:
        status = "BLOCKED" if result.is_blocked else "OK"
        print(f"  [{status}] {result}")

    if not report.all_clear:
        blocked = report.blocked_jobs()
        print(f"\n{len(blocked)} job(s) blocked.", file=sys.stderr)
        return 1
    return 0


def build_dependency_parser(subparsers) -> None:
    p: argparse.ArgumentParser = subparsers.add_parser(
        "dep-check",
        help="Check whether job dependencies are satisfied.",
    )
    p.add_argument(
        "-c", "--config",
        default="cronwatch/cronwatch.yml",
        help="Path to cronwatch.yml",
    )
    p.set_defaults(func=cmd_dep_check)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cronwatch-deps")
    sub = parser.add_subparsers(dest="command")
    build_dependency_parser(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
