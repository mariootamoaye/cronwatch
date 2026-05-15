"""CLI commands for managing job checkpoints."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.checkpoint import (
    record_checkpoint,
    list_checkpoints,
    last_checkpoint,
    clear_checkpoints,
)

_DEFAULT_PATH = Path("cronwatch_checkpoints.json")


def cmd_cp_add(args: argparse.Namespace) -> None:
    path = Path(args.file)
    entry = record_checkpoint(path, job=args.job, name=args.name, note=args.note)
    print(f"Checkpoint recorded: [{entry.job}] {entry.name} at {entry.timestamp}")


def cmd_cp_list(args: argparse.Namespace) -> None:
    path = Path(args.file)
    entries = list_checkpoints(path, job=args.job or None)
    if not entries:
        print("No checkpoints found.")
        return
    for e in entries:
        note_part = f"  # {e.note}" if e.note else ""
        print(f"{e.timestamp}  [{e.job}]  {e.name}{note_part}")


def cmd_cp_last(args: argparse.Namespace) -> None:
    path = Path(args.file)
    entry = last_checkpoint(path, job=args.job)
    if entry is None:
        print(f"No checkpoints for job '{args.job}'.")
        sys.exit(1)
    note_part = f"  # {entry.note}" if entry.note else ""
    print(f"{entry.timestamp}  {entry.name}{note_part}")


def cmd_cp_clear(args: argparse.Namespace) -> None:
    path = Path(args.file)
    removed = clear_checkpoints(path, job=args.job)
    print(f"Removed {removed} checkpoint(s) for job '{args.job}'.")


def build_checkpoint_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("checkpoint", help="Manage job checkpoints")
    p.add_argument("--file", default=str(_DEFAULT_PATH), help="Checkpoint store path")
    sub = p.add_subparsers(dest="cp_cmd", required=True)

    add = sub.add_parser("add", help="Record a checkpoint")
    add.add_argument("job", help="Job name")
    add.add_argument("name", help="Checkpoint name / stage")
    add.add_argument("--note", default=None, help="Optional note")
    add.set_defaults(func=cmd_cp_add)

    ls = sub.add_parser("list", help="List checkpoints")
    ls.add_argument("--job", default=None, help="Filter by job name")
    ls.set_defaults(func=cmd_cp_list)

    last = sub.add_parser("last", help="Show last checkpoint for a job")
    last.add_argument("job", help="Job name")
    last.set_defaults(func=cmd_cp_last)

    clr = sub.add_parser("clear", help="Clear checkpoints for a job")
    clr.add_argument("job", help="Job name")
    clr.set_defaults(func=cmd_cp_clear)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="cronwatch-checkpoint")
    parser.add_argument("--file", default=str(_DEFAULT_PATH))
    sub = parser.add_subparsers(dest="cp_cmd", required=True)
    build_checkpoint_parser(sub)
    args = parser.parse_args(argv)
    args.func(args)
