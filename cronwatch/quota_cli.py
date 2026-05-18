"""CLI sub-commands for quota management."""
from __future__ import annotations

import argparse
from pathlib import Path

from cronwatch.quota import check_quota, record_run

_DEFAULT_QUOTA_PATH = Path("~/.cronwatch/quota.json")


def _default_quota_path() -> Path:
    return _DEFAULT_QUOTA_PATH.expanduser()


def cmd_quota_check(args: argparse.Namespace) -> int:
    quota_file = Path(args.quota_file) if args.quota_file else _default_quota_path()
    result = check_quota(
        job_name=args.job,
        limit=args.limit,
        window_hours=args.window,
        quota_file=quota_file,
    )
    print(str(result))
    return 1 if result.exceeded else 0


def cmd_quota_record(args: argparse.Namespace) -> int:
    quota_file = Path(args.quota_file) if args.quota_file else _default_quota_path()
    entry = record_run(job_name=args.job, quota_file=quota_file)
    print(f"Recorded run for '{entry.job_name}' at {entry.ran_at}")
    return 0


def build_quota_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    quota_p = subparsers.add_parser("quota", help="Job execution quota commands")
    quota_sub = quota_p.add_subparsers(dest="quota_cmd", required=True)

    # quota check
    chk = quota_sub.add_parser("check", help="Check whether a job has exceeded its quota")
    chk.add_argument("job", help="Job name")
    chk.add_argument("--limit", type=int, required=True, help="Max allowed runs")
    chk.add_argument("--window", type=int, default=24, help="Rolling window in hours (default 24)")
    chk.add_argument("--quota-file", default=None, help="Path to quota JSON file")
    chk.set_defaults(func=cmd_quota_check)

    # quota record
    rec = quota_sub.add_parser("record", help="Record a job run against its quota")
    rec.add_argument("job", help="Job name")
    rec.add_argument("--quota-file", default=None, help="Path to quota JSON file")
    rec.set_defaults(func=cmd_quota_record)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cronwatch-quota")
    subs = parser.add_subparsers(dest="cmd", required=True)
    build_quota_parser(subs)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
