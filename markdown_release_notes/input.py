"""Shared validation for local JSON and exported text."""

import json
import unicodedata
from pathlib import Path


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"{value} is not valid JSON")


def load_json(path: Path) -> object:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except RecursionError as exc:
        raise ValueError("JSON nesting is too deep") from exc


def normalize_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not (words := value.split()):
        raise ValueError(f"{field} must be a non-empty string")
    if any(ch not in "\t\r\n" and unicodedata.category(ch) in {"Cc", "Cs"} for ch in value):
        raise ValueError(f"{field} contains a control character or an unpaired surrogate")
    return " ".join(words)


def parse_labels(value: object, field: str) -> frozenset[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array of non-empty strings")
    return frozenset(
        normalize_text(label, f"{field}[{index}]").casefold() for index, label in enumerate(value)
    )
