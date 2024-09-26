"""Local release notes command line interface."""

import argparse
import sys
from pathlib import Path

from .export import parse_export
from .input import load_json, parse_labels
from .release import (
    DEFAULT_LABELS,
    Release,
    parse_label_map,
    parse_metadata,
    parse_release,
)
from .render import render_json, render_notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markdown-release-notes",
        description="Render release notes from a local JSON export of merged pull requests.",
    )
    parser.add_argument("export", type=Path, help="UTF-8 JSON export file")
    parser.add_argument("--labels", type=Path, metavar="FILE", help="JSON label mapping overrides")
    parser.add_argument(
        "--include-label", action="append", default=[], metavar="LABEL",
        help="keep PRs with any of these labels (repeatable)",
    )
    parser.add_argument(
        "--exclude-label", action="append", default=[], metavar="LABEL",
        help="drop PRs with any of these labels (repeatable; overrides inclusion)",
    )
    parser.add_argument("--version", help="release identifier to show in the heading")
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="release date to show below the heading")
    parser.add_argument(
        "--metadata", type=Path, metavar="FILE", help="JSON release metadata and summary",
    )
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown",
        help="output format (default: markdown)",
    )
    args = parser.parse_args(argv)

    try:
        release = parse_release(args.version, args.date)
        included = parse_labels(args.include_label, "--include-label")
        excluded = parse_labels(args.exclude_label, "--exclude-label")
    except ValueError as exc:
        parser.error(str(exc))

    if args.metadata is not None:
        try:
            metadata = parse_metadata(load_json(args.metadata))
        except (OSError, ValueError) as exc:
            parser.exit(2, f"{parser.prog}: {str(args.metadata)!r}: {exc}\n")
        release = Release(
            version=release.version or metadata.version,
            released_on=release.released_on or metadata.released_on,
            summary=metadata.summary,
        )

    label_map = DEFAULT_LABELS
    if args.labels is not None:
        try:
            label_map = parse_label_map(load_json(args.labels))
        except (OSError, ValueError) as exc:
            parser.exit(2, f"{parser.prog}: {str(args.labels)!r}: {exc}\n")

    try:
        records = parse_export(load_json(args.export))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{parser.prog}: {str(args.export)!r}: {exc}\n")

    selected = [
        record for record in records
        if (not included or not record.labels.isdisjoint(included))
        and record.labels.isdisjoint(excluded)
    ]
    if args.format == "json":
        notes = render_json(selected, release, label_map)
    else:
        notes = render_notes(selected, release, label_map, no_matches=bool(records) and not selected)
    sys.stdout.buffer.write(notes.encode("utf-8"))
    return 0
