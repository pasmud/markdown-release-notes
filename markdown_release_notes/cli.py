"""Local release notes command line interface."""

import argparse
import sys
from pathlib import Path

from .export import parse_export
from .input import load_json
from .render import render_notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="markdown-release-notes",
        description="Render Markdown from a local JSON export of merged pull requests.",
    )
    parser.add_argument("export", type=Path, help="UTF-8 JSON export file")
    args = parser.parse_args(argv)

    try:
        records = parse_export(load_json(args.export))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"{parser.prog}: {str(args.export)!r}: {exc}\n")

    sys.stdout.buffer.write(render_notes(records).encode("utf-8"))
    return 0
