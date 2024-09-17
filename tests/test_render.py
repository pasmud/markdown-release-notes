import pytest

from markdown_release_notes.export import parse_export
from markdown_release_notes.render import render_notes


def test_render_orders_by_number_and_escapes_titles_and_destinations():
    records = parse_export([
        {"number": 2, "title": "Tidy docs\n## Heading"},
        {
            "number": 10,
            "title": "Show **preview** for <draft> & [sample]",
            "url": "https://example.invalid/changes/(draft)?x=1&copy;=2",
        },
    ])
    assert render_notes(records) == (
        "# Release notes\n\n## Other changes\n\n"
        "- [#10](<https://example.invalid/changes/(draft)?x=1&amp;copy;=2>)"
        " — Show \\*\\*preview\\*\\* for \\<draft\\> \\& \\[sample\\]\n"
        "- \\#2 — Tidy docs \\#\\# Heading\n"
    )


def test_title_does_not_supply_links_or_mentions():
    records = parse_export([{
        "number": 1,
        "title": "See https://example.invalid, www.example.invalid or fake@example.invalid",
    }])
    assert render_notes(records).endswith(
        "See https\\://example.invalid, www\\.example.invalid or fake\\@example.invalid\n"
    )


@pytest.mark.parametrize("url", [
    "http://example.invalid/1",
    "//example.invalid/1",
    "https://name@example.invalid/1",
    "https://example.invalid/path with spaces",
    "https://example.invalid/path>tail",
    "https://example.invalid/path%0a",
    "https://example.invalid/path%5C",
    "https://example.invalid/path%",
    "https://example.invalid:65536/1",
])
def test_unsafe_urls_fail_validation(url):
    with pytest.raises(ValueError, match="row 1: url must be an absolute HTTPS URL"):
        parse_export([{"number": 1, "title": "Sample", "url": url}])


def test_empty_export():
    assert render_notes(parse_export([])) == "# Release notes\n\nNo merged pull requests.\n"
