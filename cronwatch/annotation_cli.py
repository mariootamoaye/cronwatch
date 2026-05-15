"""CLI commands for managing job annotations."""
from __future__ import annotations

import argparse
from pathlib import Path

from cronwatch.annotation import add_annotation, delete_annotations, list_annotations

_DEFAULT_PATH = Path(".cronwatch") / "annotations.json"


def cmd_annotate(args: argparse.Namespace) -> None:
    path = Path(args.annotation_file)
    entry = add_annotation(
        path=path,
        job_name=args.job,
        note=args.note,
        author=args.author,
        run_id=getattr(args, "run_id", None),
    )
    print(f"Annotation added for '{entry.job_name}' by {entry.author} at {entry.created_at}")


def cmd_annotation_list(args: argparse.Namespace) -> None:
    path = Path(args.annotation_file)
    job = getattr(args, "job", None)
    run_id = getattr(args, "run_id", None)
    entries = list_annotations(path, job_name=job, run_id=run_id)
    if not entries:
        print("No annotations found.")
        return
    for a in entries:
        rid = f" [{a.run_id}]" if a.run_id else ""
        print(f"{a.created_at}  {a.job_name}{rid}  ({a.author}): {a.note}")


def cmd_annotation_delete(args: argparse.Namespace) -> None:
    path = Path(args.annotation_file)
    removed = delete_annotations(path, job_name=args.job)
    print(f"Removed {removed} annotation(s) for '{args.job}'.")


def build_annotation_parser(
    parent: argparse._SubParsersAction,
    default_path: Path = _DEFAULT_PATH,
) -> None:
    p = parent.add_parser("annotate", help="Manage job run annotations")
    p.add_argument("--annotation-file", default=str(default_path))
    sub = p.add_subparsers(dest="annotation_cmd", required=True)

    add_p = sub.add_parser("add", help="Add an annotation")
    add_p.add_argument("job", help="Job name")
    add_p.add_argument("note", help="Annotation text")
    add_p.add_argument("--author", default="unknown", help="Author name")
    add_p.add_argument("--run-id", dest="run_id", default=None)
    add_p.set_defaults(func=cmd_annotate)

    ls_p = sub.add_parser("list", help="List annotations")
    ls_p.add_argument("--job", default=None)
    ls_p.add_argument("--run-id", dest="run_id", default=None)
    ls_p.set_defaults(func=cmd_annotation_list)

    del_p = sub.add_parser("delete", help="Delete annotations for a job")
    del_p.add_argument("job", help="Job name")
    del_p.set_defaults(func=cmd_annotation_delete)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="cronwatch-annotate")
    parser.add_argument("--annotation-file", default=str(_DEFAULT_PATH))
    sub = parser.add_subparsers(dest="annotation_cmd", required=True)
    build_annotation_parser(sub)
    args = parser.parse_args(argv)
    args.func(args)
