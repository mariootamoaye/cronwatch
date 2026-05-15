"""Job run annotations — attach freeform notes to history entries."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Annotation:
    job_name: str
    note: str
    author: str
    created_at: str = field(default_factory=_now_iso)
    run_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Annotation":
        return cls(
            job_name=d["job_name"],
            note=d["note"],
            author=d["author"],
            created_at=d.get("created_at", _now_iso()),
            run_id=d.get("run_id"),
        )


def _load_raw(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_raw(path: Path, entries: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2))


def add_annotation(
    path: Path,
    job_name: str,
    note: str,
    author: str,
    run_id: Optional[str] = None,
) -> Annotation:
    entry = Annotation(job_name=job_name, note=note, author=author, run_id=run_id)
    raw = _load_raw(path)
    raw.append(entry.to_dict())
    _save_raw(path, raw)
    return entry


def list_annotations(
    path: Path,
    job_name: Optional[str] = None,
    run_id: Optional[str] = None,
) -> List[Annotation]:
    raw = _load_raw(path)
    results = [Annotation.from_dict(r) for r in raw]
    if job_name:
        results = [a for a in results if a.job_name == job_name]
    if run_id:
        results = [a for a in results if a.run_id == run_id]
    return results


def delete_annotations(path: Path, job_name: str) -> int:
    raw = _load_raw(path)
    before = len(raw)
    raw = [r for r in raw if r.get("job_name") != job_name]
    _save_raw(path, raw)
    return before - len(raw)
