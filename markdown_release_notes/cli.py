"""Local release notes command line interface."""

import argparse
import sys
from pathlib import Path

from .export import parse_export
from .input import load_json
from .release import DEFAULT_LABELS, parse_label_map, parse_release
from .render import render_notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markdown-release-notes",
        description="Render Markdown from a local JSON export of merged pull requests.",
    )
    parser.add_argument("export", type=Path, help="UTF-8 JSON export file")
    parser.add_argument("--labels", type=Path, metavar="FILE", help="JSON label mapping overrides")
    parser.add_argument("--version", help="release identifier to show in the heading")
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="release date to show below the heading")
    args = parser.parse_args(argv)

    try:
        release = parse_release(args.version, args.date)
    except ValueError as exc:
        parser.error(str(exc))

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

    sys.stdout.buffer.write(render_notes(records, release, label_map).encode("utf-8"))
    return 0
