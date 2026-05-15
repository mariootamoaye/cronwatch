"""Audit log: records configuration changes and administrative actions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_DEFAULT_PATH = Path("cronwatch_audit.jsonl")


@dataclass
class AuditEntry:
    timestamp: str
    actor: str          # e.g. "cli", "scheduler", a username
    action: str         # e.g. "snooze", "mute", "config_reload"
    target: Optional[str] = None   # job name or resource
    detail: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuditEntry":
        return cls(
            timestamp=d["timestamp"],
            actor=d["actor"],
            action=d["action"],
            target=d.get("target"),
            detail=d.get("detail"),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")


def record(
    actor: str,
    action: str,
    target: Optional[str] = None,
    detail: Optional[str] = None,
    path: Path = _DEFAULT_PATH,
) -> AuditEntry:
    """Append a new audit entry and return it."""
    entry = AuditEntry(
        timestamp=_now_iso(),
        actor=actor,
        action=action,
        target=target,
        detail=detail,
    )
    existing = _load_raw(path)
    existing.append(entry.to_dict())
    _save_raw(path, existing)
    return entry


def list_entries(
    path: Path = _DEFAULT_PATH,
    actor: Optional[str] = None,
    action: Optional[str] = None,
) -> List[AuditEntry]:
    """Return audit entries, optionally filtered by actor or action."""
    raw = _load_raw(path)
    entries = [AuditEntry.from_dict(r) for r in raw]
    if actor:
        entries = [e for e in entries if e.actor == actor]
    if action:
        entries = [e for e in entries if e.action == action]
    return entries
