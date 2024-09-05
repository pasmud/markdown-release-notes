"""Local release notes command line interface."""

import argparse
import json
import sys
from pathlib import Path

from .export import parse_export
from .render import render_notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markdown-release-notes",
        description="Render Markdown from a local JSON export of merged pull requests.",
    )
    parser.add_argument("export", type=Path, help="UTF-8 JSON export file")
    args = parser.parse_args(argv)

    try:
        records = parse_export(json.loads(args.export.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{parser.prog}: {args.export}: {exc}\n")

    sys.stdout.write(render_notes(records))
    return 0
