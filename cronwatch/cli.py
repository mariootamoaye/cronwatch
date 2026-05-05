"""Command-line entry-point for cronwatch."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.scheduler import run_all

_DEFAULT_CONFIG = Path("cronwatch/cronwatch.yml")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Lightweight cron job monitor.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        metavar="FILE",
        help="Path to YAML config file (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run jobs but do not send any alerts.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    try:
        config = load_config(args.config)
    except FileNotFoundError as exc:
        logging.error("Config file not found: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to load config: %s", exc)
        return 2

    result = run_all(config, dry_run=args.dry_run)

    if result.all_ok:
        logging.info("All jobs completed successfully.")
        return 0

    logging.warning("%d job(s) had issues.", len(result.failed))
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
