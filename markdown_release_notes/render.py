"""Deterministic Markdown rendering for validated records."""

import re

from .export import PullRequest

_MARKUP = re.compile(r"[\\`*_{}\[\]()<>#!|~&:$@]|(?<=www)\.", re.I)


def _escape(text: str) -> str:
    return _MARKUP.sub(lambda match: "\\" + match[0], text)


def _entry(record: PullRequest) -> str:
    ref = f"#{record.number}"
    if record.url:
        url = record.url.replace("&", "&amp;")
        ref = f"[{ref}](<{url}>)"
    else:
        ref = _escape(ref)
    return f"- {ref} — {_escape(record.title)}"


def render_notes(records: list[PullRequest]) -> str:
    lines = ["# Release notes", ""]
    lines.extend(_entry(row) for row in sorted(records, key=lambda row: -row.number))
    if not records:
        lines.append("No merged pull requests.")
    return "\n".join(lines) + "\n"
