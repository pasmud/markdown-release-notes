"""Deterministic release notes rendering for validated records."""

import json
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


def _group_records(
    records: list[PullRequest], label_map: Mapping[str, frozenset[str]],
) -> dict[str, list[PullRequest]]:
    groups: dict[str, list[PullRequest]] = {key: [] for key, _ in SECTIONS}
    for row in sorted(records, key=lambda row: row.number, reverse=True):
        category = next(
            (key for key, _ in SECTIONS if not row.labels.isdisjoint(label_map.get(key, ()))),
            "other",
        )
        groups[category].append(row)
    return groups


def render_notes(
    records: list[PullRequest],
    release: Release = DEFAULT_RELEASE,
    label_map: Mapping[str, frozenset[str]] = DEFAULT_LABELS,
    *,
    no_matches: bool = False,
) -> str:
    heading = f"Release {_escape(release.version)}" if release.version else "Release notes"
    blocks = [f"# {heading}"]
    if release.released_on:
        blocks.append(f"Released: {release.released_on.isoformat()}")
    if not records:
        blocks.append(
            "No merged pull requests matched the label filters."
            if no_matches else "No merged pull requests."
        )
    else:
        groups = _group_records(records, label_map)
        blocks.extend(
            f"## {title}\n\n" + "\n".join(_entry(row) for row in groups[key])
            for key, title in SECTIONS if groups[key]
        )
    return "\n\n".join(blocks) + "\n"


def render_json(
    records: list[PullRequest],
    release: Release = DEFAULT_RELEASE,
    label_map: Mapping[str, frozenset[str]] = DEFAULT_LABELS,
) -> str:
    groups = _group_records(records, label_map)
    document = {
        "schema_version": 1,
        "release": {
            "version": release.version,
            "date": release.released_on.isoformat() if release.released_on else None,
        },
        "sections": [
            {
                "id": key,
                "title": title,
                "pull_requests": [
                    {
                        "number": row.number,
                        "title": row.title,
                        "url": row.url,
                        "labels": sorted(row.labels),
                    }
                    for row in groups[key]
                ],
            }
            for key, title in SECTIONS if groups[key]
        ],
    }
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"
