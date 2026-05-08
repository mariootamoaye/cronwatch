"""Tag-based filtering for cron jobs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TagFilter:
    """Represents a set of tags to match against job configs."""
    include: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)

    def matches(self, job_tags: List[str]) -> bool:
        """Return True if job_tags satisfies include/exclude constraints."""
        tag_set = set(job_tags)

        if self.exclude and tag_set & set(self.exclude):
            return False

        if self.include and not (tag_set & set(self.include)):
            return False

        return True


def parse_tag_filter(include_raw: Optional[str], exclude_raw: Optional[str]) -> TagFilter:
    """Build a TagFilter from comma-separated CLI strings."""
    def _split(raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        return [t.strip() for t in raw.split(",") if t.strip()]

    return TagFilter(include=_split(include_raw), exclude=_split(exclude_raw))


def filter_jobs(jobs: list, tag_filter: TagFilter) -> list:
    """Return only jobs whose tags match the given TagFilter."""
    return [
        job for job in jobs
        if tag_filter.matches(getattr(job, "tags", []))
    ]
