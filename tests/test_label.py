"""Tests for cronwatch.label."""
import json
import pytest
from pathlib import Path

from cronwatch.label import (
    LabelSet,
    load_labels,
    save_labels,
    list_all_labels,
    filter_by_label,
)


@pytest.fixture()
def label_file(tmp_path: Path) -> Path:
    return tmp_path / "labels.json"


# ---------------------------------------------------------------------------
# LabelSet unit tests
# ---------------------------------------------------------------------------

def test_labelset_set_and_get():
    ls = LabelSet(job_name="backup")
    ls.set("env", "prod")
    assert ls.get("env") == "prod"


def test_labelset_remove_existing_key():
    ls = LabelSet(job_name="backup", labels={"env": "prod"})
    removed = ls.remove("env")
    assert removed is True
    assert ls.get("env") is None


def test_labelset_remove_missing_key_returns_false():
    ls = LabelSet(job_name="backup")
    assert ls.remove("nonexistent") is False


def test_labelset_round_trip():
    ls = LabelSet(job_name="sync", labels={"team": "infra", "env": "staging"})
    restored = LabelSet.from_dict(ls.to_dict())
    assert restored.job_name == ls.job_name
    assert restored.labels == ls.labels


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------

def test_load_labels_missing_file_returns_empty(label_file: Path):
    ls = load_labels(label_file, "backup")
    assert ls.job_name == "backup"
    assert ls.labels == {}


def test_save_and_load_labels(label_file: Path):
    ls = LabelSet(job_name="nightly", labels={"env": "prod"})
    save_labels(label_file, ls)
    loaded = load_labels(label_file, "nightly")
    assert loaded.labels == {"env": "prod"}


def test_save_replaces_existing_entry(label_file: Path):
    ls = LabelSet(job_name="nightly", labels={"env": "prod"})
    save_labels(label_file, ls)
    ls.set("env", "staging")
    save_labels(label_file, ls)
    loaded = load_labels(label_file, "nightly")
    assert loaded.get("env") == "staging"
    raw = json.loads(label_file.read_text())
    assert len(raw) == 1  # no duplicate entries


def test_save_empty_labels_removes_entry(label_file: Path):
    ls = LabelSet(job_name="nightly", labels={"env": "prod"})
    save_labels(label_file, ls)
    empty = LabelSet(job_name="nightly")
    save_labels(label_file, empty)
    raw = json.loads(label_file.read_text())
    assert raw == []


def test_list_all_labels(label_file: Path):
    save_labels(label_file, LabelSet(job_name="a", labels={"k": "1"}))
    save_labels(label_file, LabelSet(job_name="b", labels={"k": "2"}))
    all_ls = list_all_labels(label_file)
    names = {ls.job_name for ls in all_ls}
    assert names == {"a", "b"}


# ---------------------------------------------------------------------------
# filter_by_label
# ---------------------------------------------------------------------------

def test_filter_by_label_matches_correct_jobs(label_file: Path):
    save_labels(label_file, LabelSet(job_name="job1", labels={"env": "prod"}))
    save_labels(label_file, LabelSet(job_name="job2", labels={"env": "staging"}))
    save_labels(label_file, LabelSet(job_name="job3", labels={"env": "prod"}))
    all_ls = list_all_labels(label_file)
    result = filter_by_label(all_ls, "env", "prod")
    assert sorted(result) == ["job1", "job3"]


def test_filter_by_label_no_match(label_file: Path):
    save_labels(label_file, LabelSet(job_name="job1", labels={"env": "prod"}))
    all_ls = list_all_labels(label_file)
    assert filter_by_label(all_ls, "env", "dev") == []
