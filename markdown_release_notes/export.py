"""Validate the fields used in a local pull request export."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

_URL = re.compile(r"[a-zA-Z0-9._~:/?#@!$&'()*+,;=%-]+")
_HOST_LABEL = r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
_AUTHORITY = re.compile(rf"{_HOST_LABEL}(?:\.{_HOST_LABEL})*(?::[0-9]{{1,5}})?")
_BAD_PERCENT = re.compile(r"%(?![0-9a-fA-F]{2})|%(?:[01][0-9a-f]|7f|5c)", re.I)


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    url: str | None = None


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


def parse_export(data: object) -> list[PullRequest]:
    if not isinstance(data, list):
        raise ValueError("expected an array of pull requests")

    records = []
    for index, row in enumerate(data, start=1):
        try:
            if not isinstance(row, dict):
                raise ValueError("expected a pull request object")
            number = row.get("number")
            if type(number) is not int or number < 1:
                raise ValueError("number must be a positive integer")
            title = row.get("title")
            if not isinstance(title, str) or not (title := " ".join(title.split())):
                raise ValueError("title must be a non-empty string")
            records.append(PullRequest(number, title, _parse_url(row.get("url"))))
        except ValueError as exc:
            raise ValueError(f"row {index}: {exc}") from exc
    return records
