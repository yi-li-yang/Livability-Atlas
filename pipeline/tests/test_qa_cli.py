import json

import pytest
from typer.testing import CliRunner

from atlas.cli import app
from atlas.qa.regional import Regional
from tests.qa_sample import spoil, write_sample


@pytest.fixture(autouse=True)
def no_regional_facts(monkeypatch):
    """London's facts are about London, and the sample is seven cells of it."""
    monkeypatch.setattr("atlas.qa.report.regional_of", lambda region: Regional({}, [], []))


def run(tmp_path, *args):
    return CliRunner().invoke(app, ["qa", "london", "--data-dir", str(tmp_path), *args])


def published(tmp_path):
    return tmp_path / "published"


def latest(tmp_path) -> dict:
    path = published(tmp_path) / "london" / "latest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_command_checks_the_latest_bundle_and_writes_its_report(tmp_path):
    bundle = write_sample(published(tmp_path))
    result = run(tmp_path)
    assert result.exit_code == 0, result.output
    assert "QA passed: 13 checks, 0 warnings, 0 skipped" in result.output
    assert str(bundle / "qa.md") in result.output
    assert (bundle / "qa.md").exists()
    assert "Published" not in result.output


def test_a_check_that_fails_is_listed_and_the_command_fails(tmp_path):
    bundle = spoil(write_sample(published(tmp_path)), manifest=lambda m: m.update(cell_count=8))
    result = run(tmp_path)
    assert result.exit_code == 1
    assert "QA failed: 1 of 13 checks failed" in result.output
    assert "The rows match the manifest's cell count" in result.output
    assert (bundle / "qa.md").exists()


def test_a_warning_is_listed_but_the_command_passes(tmp_path):
    def unknown(manifest: dict) -> None:
        manifest["datasets"][0]["licence"] = "unknown"

    spoil(write_sample(published(tmp_path)), manifest=unknown)
    result = run(tmp_path)
    assert result.exit_code == 0, result.output
    assert "QA passed: 12 checks, 1 warning, 0 skipped" in result.output
    assert "Warning, Datasets: No dataset has an unknown licence" in result.output


def test_a_version_can_be_checked_without_being_published(tmp_path):
    old = write_sample(published(tmp_path))
    new = write_sample(published(tmp_path), columns={"diversity": [0.1] * 6 + [0.9]}, publish=False)
    result = run(tmp_path, "--version", new.name)
    assert result.exit_code == 0, result.output
    assert (new / "qa.md").exists()
    assert latest(tmp_path) == {"version": old.name}


def test_publish_publishes_a_version_that_passes(tmp_path):
    old = write_sample(published(tmp_path))
    new = write_sample(published(tmp_path), columns={"diversity": [0.1] * 6 + [0.9]}, publish=False)
    result = run(tmp_path, "--version", new.name, "--publish")
    assert result.exit_code == 0, result.output
    assert f"Published london {new.name}" in result.output
    assert latest(tmp_path) == {"version": new.name, "previous": old.name}


def test_publish_does_not_publish_a_version_that_fails(tmp_path):
    old = write_sample(published(tmp_path))
    new = spoil(
        write_sample(published(tmp_path), columns={"diversity": [0.1] * 6 + [0.9]}, publish=False),
        manifest=lambda m: m.update(cell_count=8),
    )
    result = run(tmp_path, "--version", new.name, "--publish")
    assert result.exit_code == 1
    assert f"london {new.name} is not published" in result.output
    assert latest(tmp_path) == {"version": old.name}


def test_there_must_be_a_bundle_to_check(tmp_path):
    result = run(tmp_path)
    assert result.exit_code == 1
    assert "no published bundle of london" in result.output
    result = run(tmp_path, "--version", "0123456789ab")
    assert result.exit_code == 1
    assert "no bundle 0123456789ab" in result.output
