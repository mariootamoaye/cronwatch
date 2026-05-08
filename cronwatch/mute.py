"""Mute (silence) alerts for specific jobs during maintenance windows."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_DEFAULT_PATH = Path("~/.cronwatch/mutes.json").expanduser()


@dataclass
class MuteEntry:
    job_name: str
    muted_until: str  # ISO-8601
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        until = datetime.fromisoformat(self.muted_until)
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
        return now < until


def _load_raw(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return json.load(fh)


def _save_raw(entries: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(entries, fh, indent=2)


def mute_job(
    job_name: str,
    until: datetime,
    reason: str = "",
    path: Path = _DEFAULT_PATH,
) -> MuteEntry:
    """Add or replace a mute entry for *job_name*."""
    entry = MuteEntry(
        job_name=job_name,
        muted_until=until.isoformat(),
        reason=reason,
    )
    raw = [r for r in _load_raw(path) if r["job_name"] != job_name]
    raw.append(asdict(entry))
    _save_raw(raw, path)
    return entry


def unmute_job(job_name: str, path: Path = _DEFAULT_PATH) -> bool:
    """Remove mute entry for *job_name*. Returns True if an entry was removed."""
    raw = _load_raw(path)
    filtered = [r for r in raw if r["job_name"] != job_name]
    if len(filtered) == len(raw):
        return False
    _save_raw(filtered, path)
    return True


def is_muted(
    job_name: str,
    now: Optional[datetime] = None,
    path: Path = _DEFAULT_PATH,
) -> bool:
    """Return True if *job_name* has an active mute."""
    for raw in _load_raw(path):
        if raw["job_name"] == job_name:
            entry = MuteEntry(**raw)
            return entry.is_active(now)
    return False


def list_mutes(
    path: Path = _DEFAULT_PATH,
    now: Optional[datetime] = None,
) -> list[MuteEntry]:
    """Return all currently active mute entries."""
    now = now or datetime.now(timezone.utc)
    return [
        MuteEntry(**r)
        for r in _load_raw(path)
        if MuteEntry(**r).is_active(now)
    ]
