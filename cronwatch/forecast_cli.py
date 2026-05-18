"""CLI sub-commands for the forecast feature."""
from __future__ import annotations

import argparse
from pathlib import Path

from cronwatch.config import load
from cronwatch.forecast import forecast_job
from cronwatch.forecast_render import render_forecast_table


def _default_history_path() -> Path:
    return Path.home() / ".cronwatch" / "history.json"


def cmd_forecast(
    args: argparse.Namespace,
    history_path: Path | None = None,
) -> int:
    cfg = load(args.config)
    hp = history_path or _default_history_path()

    job_names = (
        [args.job]
        if getattr(args, "job", None)
        else [j.name for j in cfg.jobs]
    )

    results = [forecast_job(name, hp) for name in job_names]
    print(render_forecast_table(results))
    return 0


def build_forecast_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("forecast", help="Show predicted next run times")
    p.add_argument("-c", "--config", default="cronwatch/cronwatch.yml")
    p.add_argument("job", nargs="?", help="Limit to a single job")
    p.set_defaults(func=cmd_forecast)
    return p


def main(argv=None) -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="cronwatch-forecast")
    sub = parser.add_subparsers(dest="command")
    build_forecast_parser(sub)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    raise SystemExit(args.func(args))
