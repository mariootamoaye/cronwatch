"""Tests for cronwatch.tag_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cronwatch.config import load_config
from cronwatch.tag_cli import list_tags, resolve_jobs, cmd_list_tags


YAML = textwrap.dedent("""\
    jobs:
      - name: backup
        command: backup.sh
        schedule: "0 2 * * *"
        tags: [db, nightly]
      - name: report
        command: report.sh
        schedule: "0 6 * * 1"
        tags: [report]
      - name: cleanup
        command: cleanup.sh
        schedule: "0 3 * * *"
        tags: [db]
""")


@pytest.fixture()
def cfg_file(tmp_path: Path) -> Path:
    p = tmp_path / "cronwatch.yml"
    p.write_text(YAML)
    return p


def test_list_tags_returns_sorted_unique(cfg_file):
    cfg = load_config(str(cfg_file))
    assert list_tags(cfg) == ["db", "nightly", "report"]


def test_list_tags_empty_when_no_tags(tmp_path):
    p = tmp_path / "cronwatch.yml"
    p.write_text("jobs:\n  - name: j\n    command: x\n    schedule: '* * * * *'\n")
    cfg = load_config(str(p))
    assert list_tags(cfg) == []


def test_resolve_jobs_include_filter(cfg_file):
    cfg = load_config(str(cfg_file))
    jobs = resolve_jobs(cfg, tags_raw="nightly", exclude_tags_raw=None)
    assert [j.name for j in jobs] == ["backup"]


def test_resolve_jobs_exclude_filter(cfg_file):
    cfg = load_config(str(cfg_file))
    jobs = resolve_jobs(cfg, tags_raw=None, exclude_tags_raw="db")
    assert [j.name for j in jobs] == ["report"]


def test_resolve_jobs_no_filter_returns_all(cfg_file):
    cfg = load_config(str(cfg_file))
    jobs = resolve_jobs(cfg, tags_raw=None, exclude_tags_raw=None)
    assert len(jobs) == 3


def test_cmd_list_tags_prints_tags(cfg_file, capsys):
    cmd_list_tags(str(cfg_file))
    out = capsys.readouterr().out
    assert "db" in out
    assert "nightly" in out
    assert "report" in out


def test_cmd_list_tags_no_tags_message(tmp_path, capsys):
    p = tmp_path / "cronwatch.yml"
    p.write_text("jobs:\n  - name: j\n    command: x\n    schedule: '* * * * *'\n")
    cmd_list_tags(str(p))
    out = capsys.readouterr().out
    assert "No tags defined" in out
