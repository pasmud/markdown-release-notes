import pytest

from markdown_release_notes.export import PullRequest, parse_export
from markdown_release_notes.input import load_json


@pytest.mark.parametrize(("data", "error"), [
    ({"number": 1}, "expected an array"),
    ([None], "row 1: expected a pull request object"),
    ([{"number": True, "title": "Example"}], "row 1: number must be a positive integer"),
    ([{"number": 0, "title": "Example"}], "row 1: number must be a positive integer"),
    ([{"number": 1, "title": "  "}], "row 1: title must be a non-empty string"),
    ([{"number": 1, "title": "Example\x00"}], "row 1: title contains a control character"),
    ([{"number": 1, "title": "Example\ud800"}], "row 1: title contains .* unpaired surrogate"),
    ([{"number": 1, "title": "Example", "labels": None}], "row 1: labels must be an array"),
    ([{"number": 1, "title": "Example", "labels": [42]}], r"row 1: labels\[0\] must be a non-empty string"),
    ([{"number": 1, "title": "Example", "label": []}], "row 1: unknown fields: 'label'"),
])
def test_export_rejects_invalid_shape_and_values(data, error):
    with pytest.raises(ValueError, match=error):
        parse_export(data)


def test_deduplicates_equivalent_rows_without_dropping_distinct_prs():
    rows = [
        {"number": 4, "title": "Demo\t title", "labels": ["Feature", "Review Needed", "feature"]},
        {"number": 4, "title": "Demo title", "labels": [" review  needed ", " FEATURE "], "url": None},
        {"number": 3, "title": "Demo title"},
    ]
    assert parse_export(rows) == [
        PullRequest(4, "Demo title", labels=frozenset({"feature", "review needed"})),
        PullRequest(3, "Demo title"),
    ]


@pytest.mark.parametrize("changes", [
    {"title": "A different title"},
    {"labels": ["fix"]},
    {"url": "https://example.invalid/pulls/5"},
])
def test_conflicting_duplicates_are_rejected_in_either_order(changes):
    row = {"number": 5, "title": "Demo title", "labels": ["feat"]}
    rows = [row, row | changes]
    for order in (rows, rows[::-1]):
        with pytest.raises(ValueError, match="row 2: conflicting records for PR #5"):
            parse_export(order)


@pytest.mark.parametrize(("text", "error"), [
    ('[{"number": 1, "number": 2}]', "duplicate JSON key 'number'"),
    ("[NaN]", "NaN is not valid JSON"),
    ("[Infinity]", "Infinity is not valid JSON"),
    ("[", "Expecting value"),
])
def test_load_json_reports_invalid_syntax_and_ambiguous_inputs(tmp_path, text, error):
    path = tmp_path / "export.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        load_json(path)
