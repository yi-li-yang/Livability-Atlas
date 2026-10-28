from pathlib import Path

import pytest
from pydantic import ValidationError

from atlas.catalogue.load import validate_catalogue
from atlas.catalogue.models import Region
from atlas.paths import CATALOGUE_DIR


def region(**fields):
    return {
        "id": "london",
        "name": "London",
        "country": "GB",
        "boundary": {"dataset": "ons-region-boundaries", "name": "London"},
        "grid": {"system": "h3", "resolution": 9},
        "buffer_m": 2000,
        **fields,
    }


def problem(data):
    with pytest.raises(ValidationError) as caught:
        Region.model_validate(data)
    return str(caught.value)


def test_a_region_names_its_boundary_grid_and_buffer():
    parsed = Region.model_validate(region())
    assert parsed.grid.resolution == 9
    assert parsed.buffer_m == 2000
    assert parsed.default_places == []


def test_a_country_is_a_two_letter_code():
    assert "country" in problem(region(country="Britain"))


def test_the_grid_resolution_is_one_h3_supports():
    assert "resolution" in problem(region(grid={"system": "h3", "resolution": 16}))


def test_a_buffer_cannot_be_negative():
    assert "buffer_m" in problem(region(buffer_m=-1))


def test_an_unknown_field_is_rejected():
    assert "Extra inputs are not permitted" in problem(region(centre="Bank"))


def test_a_default_place_has_a_name_and_a_position():
    places = [{"name": "Bank", "lat": 51.5133, "lng": -0.089}]
    assert Region.model_validate(region(default_places=places)).default_places[0].name == "Bank"
    assert "lat" in problem(region(default_places=[{"name": "Bank", "lat": 91, "lng": 0}]))


def write(directory: Path, region_yaml: str, name: str = "london.yaml") -> Path:
    (directory / "factors.yaml").write_text(
        "factors:\n"
        "  - {id: a, name: A, default_weight: 3, weight_reason: Why.,"
        " scales: [within-city]}\n",
        encoding="utf-8",
    )
    (directory / "datasets.yaml").write_text(
        """datasets:
  - id: ons-region-boundaries
    name: Regions
    publisher: ONS
    url: https://example.org/
    tier: country
    area: England
    resolution: regions
    date: 2025
    licence: OGL-UK-3.0
    licence_checked: 2026-10-28
    public_build: true
    attribution: ONS.
    tells: [Boundaries]
""",
        encoding="utf-8",
    )
    (directory / "regions").mkdir(exist_ok=True)
    (directory / "regions" / name).write_text(region_yaml, encoding="utf-8")
    return directory


GOOD = """
id: london
name: London
country: GB
boundary: {dataset: ons-region-boundaries, name: London}
grid: {system: h3, resolution: 9}
buffer_m: 2000
"""


def test_the_real_catalogue_has_the_london_region():
    assert (CATALOGUE_DIR / "regions" / "london.yaml").exists()
    assert validate_catalogue(CATALOGUE_DIR) == []


def test_a_region_file_passes(tmp_path):
    assert validate_catalogue(write(tmp_path, GOOD)) == []


def test_a_region_names_a_boundary_dataset_that_exists(tmp_path):
    bad = GOOD.replace("ons-region-boundaries", "nowhere")
    assert validate_catalogue(write(tmp_path, bad)) == [
        "london: datasets.yaml has no dataset nowhere."
    ]


def test_a_region_file_is_named_after_its_id(tmp_path):
    found = validate_catalogue(write(tmp_path, GOOD, name="paris.yaml"))
    assert found == ["london: the file is regions/paris.yaml, so the id must be paris."]


def test_a_problem_in_a_region_file_names_the_region(tmp_path):
    found = validate_catalogue(write(tmp_path, GOOD.replace("buffer_m: 2000", "buffer_m: -5")))
    assert len(found) == 1 and found[0].startswith("london: buffer_m")
