"""CLI sub-commands for managing job mutes."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cronwatch.mute import mute_job, unmute_job, list_mutes, _DEFAULT_PATH


def _parse_duration(value: str) -> timedelta:
    """Parse a duration string like '2h', '30m', '1d' into a timedelta."""
    units = {"m": "minutes", "h": "hours", "d": "days"}
    if not value or value[-1] not in units or not value[:-1].isdigit():
        raise argparse.ArgumentTypeError(
            f"Invalid duration '{value}'. Use e.g. 30m, 2h, 1d."
        )
    return timedelta(**{units[value[-1]]: int(value[:-1])})


def cmd_mute(args: argparse.Namespace, path: Path = _DEFAULT_PATH) -> int:
    duration: timedelta = args.duration
    until = datetime.now(timezone.utc) + duration
    entry = mute_job(args.job, until, reason=args.reason or "", path=path)
    print(f"Muted '{args.job}' until {entry.muted_until}")
    return 0


def cmd_unmute(args: argparse.Namespace, path: Path = _DEFAULT_PATH) -> int:
    removed = unmute_job(args.job, path=path)
    if removed:
        print(f"Unmuted '{args.job}'.")
    else:
        print(f"No active mute found for '{args.job}'.")
    return 0


def cmd_mute_list(args: argparse.Namespace, path: Path = _DEFAULT_PATH) -> int:  # noqa: ARG001
    entries = list_mutes(path=path)
    if not entries:
        print("No active mutes.")
        return 0
    print(f"{'JOB':<30} {'UNTIL':<26} REASON")
    print("-" * 70)
    for e in entries:
        print(f"{e.job_name:<30} {e.muted_until:<26} {e.reason}")
    return 0


def build_mute_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    mute_p = subparsers.add_parser("mute", help="Mute alerts for a job")
    mute_p.add_argument("job", help="Job name")
    mute_p.add_argument(
        "duration",
        type=_parse_duration,
        help="Duration to mute, e.g. 2h, 30m, 1d",
    )
    mute_p.add_argument("--reason", default="", help="Optional reason")
    mute_p.set_defaults(func=cmd_mute)

    unmute_p = subparsers.add_parser("unmute", help="Remove a mute for a job")
    unmute_p.add_argument("job", help="Job name")
    unmute_p.set_defaults(func=cmd_unmute)

    list_p = subparsers.add_parser("mute-list", help="List active mutes")
    list_p.set_defaults(func=cmd_mute_list)
