import json
import subprocess
import sys
from pathlib import Path

import pytest

VECTORS = Path(__file__).with_name("regression_vectors")


@pytest.mark.parametrize(
    "path", sorted(VECTORS.glob("*.json")), ids=lambda path: path.stem
)
def test_regression_vector(path, tmp_path):
    vector = json.loads(path.read_text(encoding="utf-8"))
    expected = vector["expected"]

    def save(name, data):
        target = tmp_path / f"{name}.json"
        target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return target

    args = list(vector.get("args", []))
    for key, flag in (("label_map", "--labels"), ("metadata", "--metadata")):
        if key in vector:
            args.extend((flag, str(save(key, vector[key]))))

    def run(rows, output_format):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "markdown_release_notes",
                str(save("export", rows)),
                "--format",
                output_format,
                *args,
            ],
            capture_output=True,
            check=False,
        )

    rows = vector["rows"]
    result = run(rows, "json")
    if "error" in expected:
        assert result.returncode == 2
        assert result.stdout == b""
        assert expected["error"] in result.stderr.decode("utf-8")
        return

    assert result.returncode == 0, result.stderr
    assert result.stderr == b""
    document = json.loads(result.stdout)
    sections = document["sections"]
    assert [
        [section["id"], [row["number"] for row in section["pull_requests"]]]
        for section in sections
    ] == expected["sections"]
    if "records" in expected:
        assert [
            row for section in sections for row in section["pull_requests"]
        ] == expected["records"]
    if "release" in expected:
        assert document["release"] == expected["release"]

    outputs = {"json": result.stdout}
    if "markdown" in expected or vector.get("reorder"):
        result = run(rows, "markdown")
        assert result.returncode == 0, result.stderr
        assert result.stderr == b""
        outputs["markdown"] = result.stdout
        markdown = result.stdout.decode("utf-8")
        for fragment in expected.get("markdown", []):
            assert fragment in markdown

    if vector.get("reorder"):
        reordered = [
            row | {"labels": row["labels"][::-1]} if "labels" in row else row
            for row in reversed(rows)
        ]
        for output_format, original in outputs.items():
            result = run(reordered, output_format)
            assert result.returncode == 0, result.stderr
            assert result.stderr == b""
            assert result.stdout == original
