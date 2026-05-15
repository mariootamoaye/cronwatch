"""Tests for cronwatch.annotation_render."""
from __future__ import annotations

from cronwatch.annotation import Annotation
from cronwatch.annotation_render import render_annotation_table


def _ann(
    job: str = "backup",
    note: str = "all good",
    author: str = "alice",
    run_id: str | None = None,
) -> Annotation:
    return Annotation(
        job_name=job,
        note=note,
        author=author,
        created_at="2024-06-01T12:00:00+00:00",
        run_id=run_id,
    )


def test_render_empty_returns_message() -> None:
    out = render_annotation_table([])
    assert "No annotations" in out


def test_render_includes_header_columns() -> None:
    out = render_annotation_table([_ann()])
    assert "TIMESTAMP" in out
    assert "JOB" in out
    assert "AUTHOR" in out
    assert "NOTE" in out


def test_render_includes_job_name() -> None:
    out = render_annotation_table([_ann(job="nightly-backup")])
    assert "nightly-backup" in out


def test_render_includes_note_text() -> None:
    out = render_annotation_table([_ann(note="disk was full")])
    assert "disk was full" in out


def test_render_includes_author() -> None:
    out = render_annotation_table([_ann(author="carol")])
    assert "carol" in out


def test_render_shows_run_id_when_present() -> None:
    out = render_annotation_table([_ann(run_id="abc-999")])
    assert "abc-999" in out


def test_render_shows_dash_when_no_run_id() -> None:
    out = render_annotation_table([_ann(run_id=None)])
    lines = out.splitlines()
    # data row should contain a dash placeholder
    data_row = lines[-1]
    assert "-" in data_row


def test_render_multiple_rows() -> None:
    anns = [_ann(job="job-a"), _ann(job="job-b")]
    out = render_annotation_table(anns)
    assert "job-a" in out
    assert "job-b" in out
