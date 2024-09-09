import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "markdown_release_notes", *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )


def test_documented_command_matches_expected_markdown():
    proc = run_cli(
        "examples/merged-prs.json",
        "--labels", "examples/labels.json",
        "--version", "v2.4.0-demo",
        "--date", "2030-06-12",
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == b""
    assert proc.stdout == (EXAMPLES / "release-notes.md").read_bytes()


@pytest.mark.parametrize(("content", "diagnostic"), [
    (b"[", b"line 1 column 2"),
    (b"\xff", b"utf-8"),
    (
        b'[{"number": 1, "title": "Valid row"}, {"number": 2, "title": ""}]',
        b"row 2: title must be a non-empty string",
    ),
])
def test_bad_export_reports_source_without_partial_stdout(tmp_path, content, diagnostic):
    export = tmp_path / "example.json"
    export.write_bytes(content)
    proc = run_cli(export)
    assert proc.returncode == 2
    assert proc.stdout == b""
    assert b"example.json" in proc.stderr
    assert diagnostic in proc.stderr
    assert b"Traceback" not in proc.stderr


def test_invalid_label_map_names_its_own_input(tmp_path):
    config = tmp_path / "fake-labels.json"
    config.write_text('{"unrecognized": []}', encoding="utf-8")
    proc = run_cli(EXAMPLES / "merged-prs.json", "--labels", config)
    assert proc.returncode == 2
    assert proc.stdout == b""
    assert b"fake-labels.json" in proc.stderr
    assert b"unknown categories: 'unrecognized'" in proc.stderr
    assert b"merged-prs.json" not in proc.stderr


def test_unreadable_export_reports_its_path(tmp_path):
    proc = run_cli(tmp_path / "missing.json")
    assert proc.returncode == 2
    assert proc.stdout == b""
    assert b"missing.json" in proc.stderr
    assert b"Traceback" not in proc.stderr


def test_invalid_cli_date_is_a_usage_error():
    proc = run_cli(EXAMPLES / "merged-prs.json", "--date", "2030-02-30")
    assert proc.returncode == 2
    assert proc.stdout == b""
    assert b"date must be a valid calendar date in YYYY-MM-DD format" in proc.stderr


def test_label_filters_are_repeatable_and_exclusions_win():
    proc = run_cli(
        EXAMPLES / "merged-prs.json", "--labels", EXAMPLES / "labels.json",
        "--include-label", "  TYPE:FEATURE ", "--include-label", "Docs",
        "--exclude-label", "BUGFIX", "--exclude-label", "change:incompatible",
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.decode() == (
        "# Release notes\n\n"
        "## Features\n\n- \\#206 — Add a compact summary\n\n"
        "## Other changes\n\n"
        "- [#205](<https://example.invalid/demo/pulls/205>) — Document the sample workspace\n"
    )


def test_exclude_only_keeps_unlabeled_prs(tmp_path):
    export = tmp_path / "export.json"
    export.write_text(
        '[{"number": 1, "title": "Visible"}, '
        '{"number": 2, "title": "Hidden", "labels": ["Internal  only"]}]',
        encoding="utf-8",
    )
    proc = run_cli(export, "--exclude-label", "internal only")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.decode() == "# Release notes\n\n## Other changes\n\n- \\#1 — Visible\n"


def test_label_filters_can_leave_no_matches():
    proc = run_cli(EXAMPLES / "merged-prs.json", "--include-label", "unmatched")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == b"# Release notes\n\nNo merged pull requests matched the label filters.\n"


@pytest.mark.parametrize("option", ["--include-label", "--exclude-label"])
def test_blank_filter_is_a_usage_error(option):
    proc = run_cli(EXAMPLES / "merged-prs.json", option, "  ")
    assert proc.returncode == 2
    assert proc.stdout == b""
    assert option.encode() + b"[0] must be a non-empty string" in proc.stderr


def test_filtering_does_not_hide_conflicting_rows(tmp_path):
    export = tmp_path / "export.json"
    export.write_text(
        '[{"number": 1, "title": "First", "labels": ["keep"]}, '
        '{"number": 1, "title": "Conflicting"}]',
        encoding="utf-8",
    )
    proc = run_cli(export, "--include-label", "keep")
    assert proc.returncode == 2
    assert proc.stdout == b""
    assert b"row 2: conflicting records for PR #1" in proc.stderr
