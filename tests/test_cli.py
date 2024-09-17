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
