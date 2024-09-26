"""Release metadata and label category rules."""

from dataclasses import dataclass
from datetime import date

from .input import normalize_text, parse_labels

SECTIONS = (
    ("breaking", "Breaking changes"),
    ("feat", "Features"),
    ("fix", "Fixes"),
    ("other", "Other changes"),
)
DEFAULT_LABELS = {
    "breaking": frozenset({"breaking", "breaking change", "breaking-change"}),
    "feat": frozenset({"feat", "feature", "enhancement"}),
    "fix": frozenset({"fix", "bug", "bugfix"}),
}


def parse_label_map(data: object) -> dict[str, frozenset[str]]:
    if not isinstance(data, dict):
        raise ValueError("expected an object mapping categories to label arrays")
    if unknown := data.keys() - DEFAULT_LABELS.keys():
        raise ValueError(f"unknown categories: {', '.join(map(repr, sorted(unknown)))}")
    return DEFAULT_LABELS | {key: parse_labels(value, key) for key, value in data.items()}


@dataclass(frozen=True)
class Release:
    version: str | None = None
    released_on: date | None = None
    summary: str | None = None


DEFAULT_RELEASE = Release()


def parse_release(
    version: str | None, release_date: str | None, *, summary: str | None = None,
) -> Release:
    version = normalize_text(version, "version") if version is not None else None
    summary = normalize_text(summary, "summary") if summary is not None else None
    if release_date is None:
        return Release(version, summary=summary)
    message = "date must be a valid calendar date in YYYY-MM-DD format"
    try:
        parsed = date.fromisoformat(release_date)
    except ValueError as exc:
        raise ValueError(message) from exc
    if parsed.isoformat() != release_date:
        raise ValueError(message)
    return Release(version, parsed, summary)


def parse_metadata(data: object) -> Release:
    if not isinstance(data, dict):
        raise ValueError("expected a release metadata object")
    if unknown := data.keys() - {"version", "date", "summary"}:
        raise ValueError(f"unknown metadata fields: {', '.join(map(repr, sorted(unknown)))}")
    for key, value in data.items():
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
    return parse_release(data.get("version"), data.get("date"), summary=data.get("summary"))
