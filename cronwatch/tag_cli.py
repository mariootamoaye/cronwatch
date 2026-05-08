"""CLI helpers for tag-based job filtering."""
from __future__ import annotations

import argparse
from typing import List

from cronwatch.config import CronwatchConfig, JobConfig, load_config
from cronwatch.tags import TagFilter, filter_jobs, parse_tag_filter


def add_tag_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach --tags and --exclude-tags arguments to an existing parser."""
    parser.add_argument(
        "--tags",
        metavar="TAG[,TAG]",
        default=None,
        help="Only run jobs that have ALL of these tags (comma-separated).",
    )
    parser.add_argument(
        "--exclude-tags",
        metavar="TAG[,TAG]",
        default=None,
        dest="exclude_tags",
        help="Skip jobs that have ANY of these tags (comma-separated).",
    )


def resolve_jobs(
    config: CronwatchConfig,
    tags_raw: str | None,
    exclude_tags_raw: str | None,
) -> List[JobConfig]:
    """Return filtered job list based on CLI tag arguments."""
    tag_filter = parse_tag_filter(tags_raw, exclude_tags_raw)
    return filter_jobs(config.jobs, tag_filter)


def list_tags(config: CronwatchConfig) -> List[str]:
    """Return a sorted, deduplicated list of all tags used across jobs."""
    all_tags: set[str] = set()
    for job in config.jobs:
        all_tags.update(job.tags)
    return sorted(all_tags)


def cmd_list_tags(config_path: str) -> None:
    """Print all known tags to stdout."""
    cfg = load_config(config_path)
    tags = list_tags(cfg)
    if not tags:
        print("No tags defined.")
    else:
        for tag in tags:
            print(tag)
