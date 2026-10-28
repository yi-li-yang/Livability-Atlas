import json

from typer.testing import CliRunner

from atlas.catalogue.schema import write_schemas
from atlas.cli import app


def test_it_writes_one_schema_per_file(tmp_path):
    written = write_schemas(tmp_path)
    assert sorted(path.name for path in written) == [
        "datasets.schema.json",
        "factors.schema.json",
        "region.schema.json",
    ]


def test_a_schema_describes_the_file_and_says_it_is_generated(tmp_path):
    write_schemas(tmp_path)
    schema = json.loads((tmp_path / "factors.schema.json").read_text(encoding="utf-8"))
    assert "factors" in schema["properties"]
    assert "Do not edit" in schema["$comment"]


def test_writing_twice_gives_the_same_bytes_with_unix_line_endings(tmp_path):
    first = [path.read_bytes() for path in write_schemas(tmp_path)]
    second = [path.read_bytes() for path in write_schemas(tmp_path)]
    assert first == second
    assert all(b"\r" not in text for text in first)


def test_the_command_writes_to_the_folder_it_is_given(tmp_path):
    result = CliRunner().invoke(app, ["schemas", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "factors.schema.json").exists()
