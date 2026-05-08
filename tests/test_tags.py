"""Tests for cronwatch.tags and cronwatch.tag_cli."""
from __future__ import annotations

import pytest

from cronwatch.tags import TagFilter, filter_jobs, parse_tag_filter
from cronwatch.config import JobConfig


def _job(name: str, tags: list) -> JobConfig:
    return JobConfig(name=name, command="true", schedule="* * * * *", tags=tags)


# ---------------------------------------------------------------------------
# TagFilter.matches
# ---------------------------------------------------------------------------

def test_empty_filter_matches_everything():
    f = TagFilter()
    assert f.matches([]) is True
    assert f.matches(["db", "nightly"]) is True


def test_include_requires_at_least_one_matching_tag():
    f = TagFilter(include=["db"])
    assert f.matches(["db", "nightly"]) is True
    assert f.matches(["nightly"]) is False
    assert f.matches([]) is False


def test_exclude_blocks_any_matching_tag():
    f = TagFilter(exclude=["skip"])
    assert f.matches(["db"]) is True
    assert f.matches(["skip", "db"]) is False


def test_include_and_exclude_combined():
    f = TagFilter(include=["db"], exclude=["skip"])
    assert f.matches(["db"]) is True
    assert f.matches(["db", "skip"]) is False
    assert f.matches(["skip"]) is False


# ---------------------------------------------------------------------------
# parse_tag_filter
# ---------------------------------------------------------------------------

def test_parse_tag_filter_none_inputs():
    f = parse_tag_filter(None, None)
    assert f.include == []
    assert f.exclude == []


def test_parse_tag_filter_comma_separated():
    f = parse_tag_filter("db,nightly", "skip, broken")
    assert f.include == ["db", "nightly"]
    assert f.exclude == ["skip", "broken"]


# ---------------------------------------------------------------------------
# filter_jobs
# ---------------------------------------------------------------------------

def test_filter_jobs_include():
    jobs = [
        _job("a", ["db"]),
        _job("b", ["nightly"]),
        _job("c", ["db", "nightly"]),
    ]
    result = filter_jobs(jobs, TagFilter(include=["db"]))
    assert [j.name for j in result] == ["a", "c"]


def test_filter_jobs_exclude():
    jobs = [
        _job("a", ["db"]),
        _job("b", ["skip"]),
        _job("c", ["db", "skip"]),
    ]
    result = filter_jobs(jobs, TagFilter(exclude=["skip"]))
    assert [j.name for j in result] == ["a"]


def test_filter_jobs_no_tags_attribute():
    """Objects without .tags should be treated as having no tags."""
    class Bare:
        name = "bare"

    result = filter_jobs([Bare()], TagFilter())
    assert len(result) == 1
