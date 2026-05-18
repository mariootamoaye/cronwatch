"""CLI commands for inspecting and managing baseline duration data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cronwatch.baseline import check_baseline, compute_stats, record_duration

_DEFAULT_BASELINE_PATH = Path(".cronwatch/baseline.json")


def cmd_baseline_stats(args: argparse.Namespace) -> None:
    path = Path(args.baseline_file)
    stats = compute_stats(args.job, path)
    if stats is None:
        print(f"No baseline data for '{args.job}' (need at least 2 samples).")
        return
    print(f"Job:          {stats.job_name}")
    print(f"Samples:      {stats.sample_count}")
    print(f"Mean:         {stats.mean_seconds:.2f}s")
    print(f"Std dev:      {stats.stddev_seconds:.2f}s")
    print(f"Upper bound:  {stats.upper_bound:.2f}s  (mean + 2σ)")


def cmd_baseline_check(args: argparse.Namespace) -> None:
    path = Path(args.baseline_file)
    result = check_baseline(args.job, args.duration, path)
    status = "ANOMALOUS" if result.anomalous else "OK"
    print(f"{args.job}: {args.duration:.2f}s — {status}")
    if result.stats and result.anomalous:
        print(f"  (upper bound: {result.stats.upper_bound:.2f}s)")


def cmd_baseline_record(args: argparse.Namespace) -> None:
    path = Path(args.baseline_file)
    record_duration(args.job, args.duration, path)
    print(f"Recorded {args.duration:.2f}s for '{args.job}'.")


def cmd_baseline_dump(args: argparse.Namespace) -> None:
    path = Path(args.baseline_file)
    if not path.exists():
        print("No baseline file found.")
        return
    with path.open() as fh:
        data = json.load(fh)
    for job, samples in sorted(data.items()):
        print(f"{job}: {len(samples)} sample(s), last={samples[-1]:.2f}s")


def build_baseline_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("baseline", help="Manage job duration baselines")
    p.add_argument("--baseline-file", default=str(_DEFAULT_BASELINE_PATH))
    sub = p.add_subparsers(dest="baseline_cmd", required=True)

    ps = sub.add_parser("stats", help="Show baseline stats for a job")
    ps.add_argument("job")
    ps.set_defaults(func=cmd_baseline_stats)

    pc = sub.add_parser("check", help="Check if a duration is anomalous")
    pc.add_argument("job")
    pc.add_argument("duration", type=float)
    pc.set_defaults(func=cmd_baseline_check)

    pr = sub.add_parser("record", help="Record a duration sample")
    pr.add_argument("job")
    pr.add_argument("duration", type=float)
    pr.set_defaults(func=cmd_baseline_record)

    pd = sub.add_parser("dump", help="Dump all baseline data")
    pd.set_defaults(func=cmd_baseline_dump)


def main() -> None:
    parser = argparse.ArgumentParser(prog="cronwatch-baseline")
    parser.add_argument("--baseline-file", default=str(_DEFAULT_BASELINE_PATH))
    sub = parser.add_subparsers(dest="baseline_cmd", required=True)
    build_baseline_parser(sub)  # type: ignore[arg-type]
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
