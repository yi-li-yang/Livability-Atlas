from pathlib import Path

from atlas.catalogue.load import validate_catalogue
from atlas.paths import CATALOGUE_DIR


def write(directory: Path, factors: str, datasets: str = "datasets: []\n") -> Path:
    (directory / "factors.yaml").write_text(factors, encoding="utf-8")
    (directory / "datasets.yaml").write_text(datasets, encoding="utf-8")
    return directory


def test_the_real_catalogue_passes():
    assert validate_catalogue(CATALOGUE_DIR) == []


def test_a_problem_names_the_factor_it_concerns(tmp_path):
    factors = """
factors:
  - id: safety
    name: Safety
    default_weight: 9
    weight_reason: Why.
    scales: [within-city]
"""
    assert validate_catalogue(write(tmp_path, factors)) == [
        "safety: default_weight: Input should be less than or equal to 5."
    ]


def test_an_unknown_field_is_named(tmp_path):
    factors = """
factors:
  - id: safety
    name: Safety
    default_weight: 3
    weight_reason: Why.
    scales: [within-city]
    colour: red
"""
    assert validate_catalogue(write(tmp_path, factors)) == ["safety: unknown field colour."]


def test_a_rule_that_spans_records_is_reported(tmp_path):
    factors = """
factors:
  - id: safety
    name: Safety
    default_weight: 3
    scales: [within-city]
"""
    assert validate_catalogue(write(tmp_path, factors)) == [
        "safety: a top-level factor needs a weight_reason (D14)."
    ]


def test_yaml_that_does_not_parse_is_a_problem_not_a_crash(tmp_path):
    found = validate_catalogue(write(tmp_path, "factors: [unclosed\n"))
    assert len(found) == 1 and found[0].startswith("factors.yaml: is not valid YAML")


def test_a_missing_file_is_a_problem_not_a_crash(tmp_path):
    (tmp_path / "datasets.yaml").write_text("datasets: []\n", encoding="utf-8")
    found = validate_catalogue(tmp_path)
    assert len(found) == 1 and found[0].startswith("factors.yaml: cannot be read")
