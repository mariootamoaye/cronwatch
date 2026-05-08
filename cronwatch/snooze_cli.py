"""CLI helpers for managing snoozes (invoked from cronwatch.cli)."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cronwatch.snooze import (
    _DEFAULT_PATH,
    clear_snooze,
    is_snoozed,
    load_all,
    snooze_job,
)


def _parse_duration(value: str) -> timedelta:
    """Parse a simple duration string like '2h', '30m', '1d'."""
    units = {"m": "minutes", "h": "hours", "d": "days"}
    if value[-1] not in units:
        raise argparse.ArgumentTypeError(
            f"Unknown duration unit '{value[-1]}'. Use m/h/d."
        )
    try:
        amount = int(value[:-1])
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid duration: {value!r}")
    return timedelta(**{units[value[-1]]: amount})


def cmd_snooze(args: argparse.Namespace, path: Path = _DEFAULT_PATH) -> int:
    delta = _parse_duration(args.duration)
    until = datetime.now(timezone.utc) + delta
    snooze_job(args.job, until, path=path)
    print(f"Snoozed '{args.job}' until {until.strftime('%Y-%m-%d %H:%M UTC')}")
    return 0


def cmd_unsnooze(args: argparse.Namespace, path: Path = _DEFAULT_PATH) -> int:
    removed = clear_snooze(args.job, path=path)
    if removed:
        print(f"Snooze cleared for '{args.job}'.")
        return 0
    print(f"No active snooze found for '{args.job}'.")
    return 1


def cmd_snooze_list(_args: argparse.Namespace, path: Path = _DEFAULT_PATH) -> int:
    entries = load_all(path=path)
    now = datetime.now(timezone.utc)
    if not entries:
        print("No snoozes recorded.")
        return 0
    for name, entry in sorted(entries.items()):
        status = "active" if entry.is_active(now) else "expired"
        print(f"  {name:30s}  until {entry.until.strftime('%Y-%m-%d %H:%M UTC')}  [{status}]")
    return 0


def build_snooze_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_snooze = sub.add_parser("snooze", help="Suppress alerts for a job temporarily")
    p_snooze.add_argument("job", help="Job name")
    p_snooze.add_argument("duration", help="Duration, e.g. 2h, 30m, 1d")
    p_snooze.set_defaults(func=cmd_snooze)

    p_unsnooze = sub.add_parser("unsnooze", help="Remove a snooze")
    p_unsnooze.add_argument("job", help="Job name")
    p_unsnooze.set_defaults(func=cmd_unsnooze)

    p_list = sub.add_parser("snooze-list", help="List all snoozes")
    p_list.set_defaults(func=cmd_snooze_list)
