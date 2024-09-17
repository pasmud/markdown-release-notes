"""Deterministic Markdown rendering for validated records."""

import re
from collections.abc import Mapping

from .export import PullRequest
from .release import DEFAULT_LABELS, DEFAULT_RELEASE, SECTIONS, Release

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


def render_notes(
    records: list[PullRequest],
    release: Release = DEFAULT_RELEASE,
    label_map: Mapping[str, frozenset[str]] = DEFAULT_LABELS,
) -> str:
    heading = f"Release {_escape(release.version)}" if release.version else "Release notes"
    blocks = [f"# {heading}"]
    if release.released_on:
        blocks.append(f"Released: {release.released_on.isoformat()}")
    if not records:
        blocks.append("No merged pull requests.")
    else:
        groups: dict[str, list[str]] = {key: [] for key, _ in SECTIONS}
        for row in sorted(records, key=lambda row: row.number, reverse=True):
            category = next(
                (key for key, _ in SECTIONS if not row.labels.isdisjoint(label_map.get(key, ()))),
                "other",
            )
            groups[category].append(_entry(row))
        blocks.extend(
            f"## {title}\n\n" + "\n".join(groups[key]) for key, title in SECTIONS if groups[key]
        )
    return "\n\n".join(blocks) + "\n"
