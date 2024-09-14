"""Validate the fields used in a local pull request export."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .input import normalize_text

_URL = re.compile(r"[a-zA-Z0-9._~:/?#@!$&'()*+,;=%-]+")
_HOST_LABEL = r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
_AUTHORITY = re.compile(rf"{_HOST_LABEL}(?:\.{_HOST_LABEL})*(?::[0-9]{{1,5}})?")
_BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})|%(?:[01][0-9a-f]|7f|5c)", re.I)
_FIELDS = {"number", "title", "url", "labels"}


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    url: str | None = None
    labels: frozenset[str] = frozenset()


def _parse_url(value: object) -> str | None:
    if value is None:
        return None
    message = "url must be an absolute HTTPS URL without credentials or unsafe characters"
    if not isinstance(value, str) or not _URL.fullmatch(value) or _BAD_PERCENT.search(value):
        raise ValueError(message)
    parts = urlsplit(value)
    if parts.scheme != "https" or not _AUTHORITY.fullmatch(parts.netloc):
        raise ValueError(message)
    _, separator, port = parts.netloc.partition(":")
    if separator and not 1 <= int(port) <= 65535:
        raise ValueError(message)
    return value


def parse_labels(value: object) -> frozenset[str]:
    if not isinstance(value, list):
        raise ValueError("labels must be an array of non-empty strings")
    return frozenset(
        normalize_text(label, f"labels[{index}]").casefold() for index, label in enumerate(value)
    )


def parse_export(data: object) -> list[PullRequest]:
    if not isinstance(data, list):
        raise ValueError("expected an array of pull requests")

    records: dict[int, PullRequest] = {}
    for index, row in enumerate(data, start=1):
        try:
            if not isinstance(row, dict):
                raise ValueError("expected a pull request object")
            if unknown := row.keys() - _FIELDS:
                raise ValueError(f"unknown fields: {', '.join(map(repr, sorted(unknown)))}")
            number = row.get("number")
            if type(number) is not int or number < 1:
                raise ValueError("number must be a positive integer")
            record = PullRequest(
                number=number,
                title=normalize_text(row.get("title"), "title"),
                url=_parse_url(row.get("url")),
                labels=parse_labels(row.get("labels", [])),
            )
            if number in records and records[number] != record:
                raise ValueError(f"conflicting records for PR #{number}")
            records[number] = record
        except ValueError as exc:
            raise ValueError(f"row {index}: {exc}") from exc
    return list(records.values())
