from typer.testing import CliRunner

from atlas.cli import app

runner = CliRunner()


def test_help_runs():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Livability Atlas" in result.output
