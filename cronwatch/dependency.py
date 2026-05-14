"""Job dependency tracking: skip a job if its upstream dependencies failed."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.history import load_recent


@dataclass
class DependencyResult:
    job_name: str
    blocked_by: List[str] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return len(self.blocked_by) > 0

    def __str__(self) -> str:
        if self.is_blocked:
            return f"{self.job_name} blocked by: {', '.join(self.blocked_by)}"
        return f"{self.job_name} dependencies satisfied"


@dataclass
class DependencyReport:
    results: List[DependencyResult] = field(default_factory=list)

    @property
    def all_clear(self) -> bool:
        return all(not r.is_blocked for r in self.results)

    def blocked_jobs(self) -> List[str]:
        return [r.job_name for r in self.results if r.is_blocked]


def check_dependencies(
    job_name: str,
    depends_on: List[str],
    history_dir: str,
    lookback: int = 1,
) -> DependencyResult:
    """Return a DependencyResult indicating which upstream jobs last failed."""
    blocked_by: List[str] = []
    for dep in depends_on:
        entries = load_recent(history_dir, dep, n=lookback)
        if not entries:
            # No history means the dependency has never run — treat as blocked.
            blocked_by.append(dep)
            continue
        last = entries[-1]
        if last.exit_code != 0:
            blocked_by.append(dep)
    return DependencyResult(job_name=job_name, blocked_by=blocked_by)


def check_all_dependencies(
    jobs: Dict[str, List[str]],
    history_dir: str,
    lookback: int = 1,
) -> DependencyReport:
    """Check dependencies for every job in the mapping {job_name: [dep, ...]}."""
    results = [
        check_dependencies(name, deps, history_dir, lookback)
        for name, deps in jobs.items()
    ]
    return DependencyReport(results=results)
