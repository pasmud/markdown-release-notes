# Markdown Release Notes

Turn a local JSON export of merged pull requests from one repository into Markdown release notes. The renderer uses only local files and the Python standard library; it does not fetch pull requests or open links.

> All examples are synthetic.

## Quick start

With Python 3.11 or newer, run from the repository root:

```sh
python -m markdown_release_notes examples/merged-prs.json \
  --labels examples/labels.json --version v2.4.0-demo --date 2030-06-12
```

See the [export](examples/merged-prs.json), [label overrides](examples/labels.json), and [expected Markdown](examples/release-notes.md). The example includes overlapping labels, an equivalent duplicate, a PR without a link, and punctuation rendered as literal text.

## Export format

Supply a UTF-8 JSON array of already-merged PRs. This is a narrow schema for sanitized data, not the raw response from a hosting API. Filter for merged PRs and keep only these fields before running the tool:

| Field | Type | Meaning |
| --- | --- | --- |
| `number` | positive integer, required | PR identifier, unique within the source repository |
| `title` | non-empty string, required | Display title; whitespace is collapsed |
| `labels` | array of non-empty strings, optional | Defaults to `[]`; whitespace is collapsed and matching is case-insensitive |
| `url` | string or `null`, optional | Absolute HTTPS link; omitted and `null` both render a plain PR number |

```json
[
  {"number": 12, "title": "Add sample previews", "labels": ["feature"]}
]
```

Unknown fields, invalid values, and repeated JSON keys are errors. Rows with the same PR number are collapsed if their normalized titles and label sets match and their URLs are identical (or both absent). Conflicting records for one PR number are errors rather than silently choosing a row.

## Label categories and order

Each PR goes in the first matching category below. Unlabeled or unmatched PRs go under **Other changes**. Empty sections are omitted, and PRs within each section sort by descending number. Equivalent exports produce identical Markdown regardless of row or label order.

| Priority | Mapping key | Default labels |
| --- | --- | --- |
| 1. Breaking changes | `breaking` | `breaking`, `breaking change`, `breaking-change` |
| 2. Features | `feat` | `feat`, `feature`, `enhancement` |
| 3. Fixes | `fix` | `fix`, `bug`, `bugfix` |
| 4. Other changes | fallback | no label required |

`--labels FILE` reads a UTF-8 JSON object. Each key replaces that category's default label list; omitted keys keep their defaults, and `[]` disables matching for that category. The only supported keys are `breaking`, `feat`, and `fix`. If a label appears in multiple categories, the same priority order applies regardless of key order in the file.

## CLI output and errors

- `--version VALUE` sets the heading to `Release VALUE`; it can be any non-empty identifier, not necessarily SemVer. With no version, the heading is `Release notes`.
- `--date YYYY-MM-DD` adds a release date below the heading. Invalid calendar dates are rejected; no date is inferred.
- Successful runs exit `0` and write UTF-8 Markdown with LF line endings to stdout. An empty export prints `No merged pull requests.` beneath the heading. Use shell redirection if you need a file.
- Invalid arguments, unreadable input files, invalid JSON, and invalid records exit `2` with a diagnostic on stderr and no Markdown on stdout. Record diagnostics identify the one-based row number. `--help` shows the CLI usage.

Titles and versions are escaped as Markdown text. Link destinations accept ASCII HTTPS URLs with DNS-style hostnames and optional ports, with no credentials, whitespace, unsafe delimiters, or malformed escapes. A rejected URL fails validation; use `null` for a PR without a usable link. The CLI validates link syntax only; use sanitized links you trust, since it does not verify destinations or follow redirects.
