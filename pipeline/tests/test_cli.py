from typer.testing import CliRunner

from atlas.cli import app

runner = CliRunner()


def test_help_runs():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Livability Atlas" in result.output


def test_validate_passes_on_the_real_catalogue():
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0
    assert "The catalogue passes." in result.output


def test_validate_lists_every_problem_and_fails(tmp_path):
    (tmp_path / "factors.yaml").write_text("factors: []\n", encoding="utf-8")
    (tmp_path / "datasets.yaml").write_text("datasets: 3\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", "--catalogue-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "factors.yaml" in result.output and "datasets.yaml" in result.output
    assert "2 problems" in result.output


def test_validate_says_problem_in_the_singular(tmp_path):
    (tmp_path / "factors.yaml").write_text("factors: []\n", encoding="utf-8")
    (tmp_path / "datasets.yaml").write_text("datasets: []\n", encoding="utf-8")
    result = runner.invoke(app, ["validate", "--catalogue-dir", str(tmp_path)])
    assert "1 problem in" in result.output
