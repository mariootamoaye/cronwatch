"""CLI commands for inspecting the cronwatch audit log."""
from __future__ import annotations

import argparse
from pathlib import Path

from cronwatch.audit import list_entries

_DEFAULT_PATH = Path("cronwatch_audit.jsonl")


def cmd_audit_list(args: argparse.Namespace) -> int:
    path = Path(args.file)
    entries = list_entries(
        path=path,
        actor=args.actor or None,
        action=args.action or None,
    )
    if not entries:
        print("No audit entries found.")
        return 0
    header = f"{'TIMESTAMP':<32} {'ACTOR':<16} {'ACTION':<20} {'TARGET':<20} DETAIL"
    print(header)
    print("-" * len(header))
    for e in entries:
        target = e.target or "-"
        detail = e.detail or "-"
        print(f"{e.timestamp:<32} {e.actor:<16} {e.action:<20} {target:<20} {detail}")
    return 0


def build_audit_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("audit", help="View the cronwatch audit log")
    sub = p.add_subparsers(dest="audit_cmd", required=True)

    ls = sub.add_parser("list", help="List audit log entries")
    ls.add_argument(
        "--file",
        default=str(_DEFAULT_PATH),
        help="Path to audit log file (default: %(default)s)",
    )
    ls.add_argument("--actor", default="", help="Filter by actor")
    ls.add_argument("--action", default="", help="Filter by action")
    ls.set_defaults(func=cmd_audit_list)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cronwatch-audit")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_audit_parser(sub)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
