"""CLI commands for replaying dead-letter queue entries."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.config import load
from cronwatch.replay import run_replay


def _default_dl_path() -> str:
    return str(Path.home() / ".cronwatch" / "deadletter.json")


def cmd_replay(args: argparse.Namespace) -> int:
    cfg = load(args.config)
    jobs = {j.name: j for j in cfg.jobs}
    dl_path = args.dl_path or _default_dl_path()

    report = run_replay(
        dl_path,
        jobs,
        purge_on_success=not args.keep,
    )

    if not report.results:
        print("No replayable entries found in dead-letter queue.")
        return 0

    for result in report.results:
        print(str(result))
        if result.error:
            print(f"  error: {result.error}", file=sys.stderr)
        if result.stderr:
            print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)

    print(f"\nReplayed {report.total} job(s): {report.succeeded} succeeded, {report.failed} failed.")
    return 0 if report.all_ok else 1


def build_replay_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("replay", help="Replay jobs from the dead-letter queue")
    p.add_argument("--config", default="cronwatch/cronwatch.yml", help="Path to config file")
    p.add_argument("--dl-path", default=None, help="Path to dead-letter JSON file")
    p.add_argument(
        "--keep",
        action="store_true",
        default=False,
        help="Do not remove successfully replayed entries from the queue",
    )
    p.set_defaults(func=cmd_replay)
    return p


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Replay dead-letter queue entries")
    sub = parser.add_subparsers(dest="command")
    build_replay_parser(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
