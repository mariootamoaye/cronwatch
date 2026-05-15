"""Job label management — attach arbitrary key=value metadata to jobs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LabelSet:
    """A mapping of label keys to values for a single job."""
    job_name: str
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> Optional[str]:
        return self.labels.get(key)

    def set(self, key: str, value: str) -> None:
        self.labels[key] = value

    def remove(self, key: str) -> bool:
        if key in self.labels:
            del self.labels[key]
            return True
        return False

    def to_dict(self) -> dict:
        return {"job": self.job_name, "labels": dict(self.labels)}

    @classmethod
    def from_dict(cls, data: dict) -> "LabelSet":
        return cls(job_name=data["job"], labels=dict(data.get("labels", {})))


def _load_all(path: Path) -> List[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_all(path: Path, records: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2))


def load_labels(path: Path, job_name: str) -> LabelSet:
    """Load the LabelSet for *job_name* from *path*, or return an empty one."""
    for record in _load_all(path):
        if record.get("job") == job_name:
            return LabelSet.from_dict(record)
    return LabelSet(job_name=job_name)


def save_labels(path: Path, label_set: LabelSet) -> None:
    """Persist *label_set*, replacing any existing entry for the same job."""
    records = [r for r in _load_all(path) if r.get("job") != label_set.job_name]
    if label_set.labels:  # only persist if there is at least one label
        records.append(label_set.to_dict())
    _save_all(path, records)


def list_all_labels(path: Path) -> List[LabelSet]:
    """Return LabelSet objects for every job that has labels stored."""
    return [LabelSet.from_dict(r) for r in _load_all(path)]


def filter_by_label(label_sets: List[LabelSet], key: str, value: str) -> List[str]:
    """Return job names whose labels contain *key* = *value*."""
    return [
        ls.job_name
        for ls in label_sets
        if ls.get(key) == value
    ]
