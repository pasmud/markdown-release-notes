import pytest

from markdown_release_notes.export import parse_export
from markdown_release_notes.release import parse_label_map, parse_release
from markdown_release_notes.render import render_notes


def test_default_precedence_and_output_are_independent_of_input_order():
    rows = [
        {"number": 11, "title": "Refine output", "labels": ["Enhancement", "fix"]},
        {"number": 2, "title": "Replace format", "labels": ["feat", "Breaking   Change", "bug"]},
        {"number": 13, "title": "Explain examples", "labels": ["docs"]},
        {"number": 12, "title": "Add export", "labels": ["feature"]},
        {"number": 3, "title": "Repair preview", "labels": ["bugfix"]},
    ]
    expected = (
        "# Release notes\n\n"
        "## Breaking changes\n\n- \\#2 — Replace format\n\n"
        "## Features\n\n- \\#12 — Add export\n- \\#11 — Refine output\n\n"
        "## Fixes\n\n- \\#3 — Repair preview\n\n"
        "## Other changes\n\n- \\#13 — Explain examples\n"
    )
    assert render_notes(parse_export(rows)) == expected
    assert render_notes(parse_export(rows[::-1])) == expected


def test_overrides_replace_only_named_defaults_and_allow_shared_aliases():
    label_map = parse_label_map({"fix": ["CUSTOM"], "feat": [" custom "], "breaking": []})
    rows = parse_export([
        {"number": 3, "title": "New preview", "labels": ["custom", "breaking"]},
        {"number": 2, "title": "Old alias", "labels": ["feat", "fix"]},
        {"number": 1, "title": "Old breaking alias", "labels": ["breaking"]},
    ])
    assert render_notes(rows, label_map=label_map) == (
        "# Release notes\n\n## Features\n\n- \\#3 — New preview\n\n"
        "## Other changes\n\n- \\#2 — Old alias\n- \\#1 — Old breaking alias\n"
    )
    assert parse_label_map({"fix": []})["feat"] == {"feat", "feature", "enhancement"}


@pytest.mark.parametrize(("data", "error"), [
    ([], "expected an object"),
    ({"feature": ["feature"]}, "unknown categories: 'feature'"),
    ({"fix": "bug"}, "fix must be an array"),
    ({"feat": ["  "]}, r"feat\[0\] must be a non-empty string"),
])
def test_invalid_label_maps(data, error):
    with pytest.raises(ValueError, match=error):
        parse_label_map(data)


def test_metadata_is_optional_literal_text_and_work_with_empty_exports():
    release = parse_release("  v2.0\n[demo]  ", "2032-02-29")
    assert render_notes([], release) == (
        "# Release v2.0 \\[demo\\]\n\nReleased: 2032-02-29\n\nNo merged pull requests.\n"
    )
    assert render_notes([], parse_release(None, "2030-06-12")).startswith(
        "# Release notes\n\nReleased: 2030-06-12\n"
    )
    assert render_notes([], parse_release("canary", None)).startswith("# Release canary\n")


@pytest.mark.parametrize("value", ["2031-02-29", "2030-6-12", "20300612", "2030-W24-3", "today"])
def test_date_requires_exact_calendar_format(value):
    with pytest.raises(ValueError, match="valid calendar date in YYYY-MM-DD format"):
        parse_release(None, value)
