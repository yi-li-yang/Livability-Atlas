import math

import numpy as np
import pytest

from atlas.qa.cells import read_cells
from tests.qa_sample import CELLS, PLACES, SOHO, sample_neighbourhoods, write_sample


@pytest.fixture
def cells(tmp_path):
    return read_cells(write_sample(tmp_path), PLACES)


def test_a_bundle_is_read_with_its_manifest_and_its_cells(cells):
    assert cells.count == len(CELLS) == 7
    assert cells.manifest.region.id == "london"
    assert cells.manifest.cell_count == 7


def test_the_value_columns_leave_out_the_cell_and_the_neighbourhood(cells):
    assert "cell" not in cells.columns and "neighbourhood" not in cells.columns
    assert {"service_level", "station_proximity", "faith__hindu", "faith__sikh"} <= set(
        cells.columns
    )


def test_numbers_are_floats_with_nan_where_a_cell_has_no_value(tmp_path):
    cells = read_cells(
        write_sample(tmp_path, columns={"station-proximity": [2, None, 5, 8, 12, 15, 30]})
    )
    minutes = cells.numbers("station_proximity")
    assert minutes.dtype == np.float64
    assert math.isnan(minutes[1]) and minutes[0] == 2.0 and minutes[6] == 30.0


def test_a_column_of_text_has_no_numbers_but_its_text(cells):
    assert cells.text("service_level")[0] == "6b"
    with pytest.raises(TypeError, match="service_level"):
        cells.numbers("service_level")
    with pytest.raises(TypeError, match="station_proximity"):
        cells.text("station_proximity")


def test_a_column_the_bundle_lacks_is_an_error(cells):
    assert not cells.has("service_level", "nope")
    assert cells.has("service_level", "faith__hindu", "neighbourhood")
    assert not cells.has("neighbourhood", "nope")
    with pytest.raises(KeyError, match="nope"):
        cells.numbers("nope")


def test_the_numbers_of_a_column_are_read_once_and_cannot_be_changed(cells):
    first = cells.numbers("station_proximity")
    assert cells.numbers("station_proximity") is first
    with pytest.raises(ValueError, match="read-only"):
        first[0] = 99.0
    assert cells.texts() is cells.texts() and "service_level" in cells.texts()


def test_valued_says_which_cells_have_a_value_for_text_and_numbers_alike(tmp_path):
    cells = read_cells(
        write_sample(
            tmp_path,
            columns={
                "station-proximity": [2, None, 5, 8, 12, 15, 30],
                "service-level": [None, "6a", "5", "4", "3", "2", "1b"],
            },
        )
    )
    assert list(cells.valued("station_proximity")) == [True, False, True, True, True, True, True]
    assert list(cells.valued("service_level")) == [False, True, True, True, True, True, True]


def test_scored_gives_a_text_column_the_scores_of_its_lookup_curve(cells):
    scored = cells.scored("service_level")
    assert scored[0] == 1.0 and scored[1] == 0.875 and scored[6] == 0.25
    assert list(cells.scored("station_proximity")) == list(cells.numbers("station_proximity"))


def test_a_place_is_the_cell_at_its_coordinates(cells):
    assert cells.cell_of("Soho") == SOHO
    assert (
        cells.at("Soho", "station_proximity")
        == cells.numbers("station_proximity")[CELLS.index(SOHO)]
    )
    assert cells.text_at("Soho", "service_level") == cells.text("service_level")[CELLS.index(SOHO)]


def test_a_place_that_is_not_named_or_not_in_the_bundle_is_an_error(tmp_path):
    cells = read_cells(write_sample(tmp_path), {**PLACES, "Paris": (48.8566, 2.3522)})
    with pytest.raises(KeyError, match="Atlantis"):
        cells.at("Atlantis", "station_proximity")
    with pytest.raises(KeyError, match="Paris"):
        cells.at("Paris", "station_proximity")


def test_the_neighbourhood_of_a_place_is_its_name_and_its_borough(cells):
    index = CELLS.index(SOHO)
    expected = sample_neighbourhoods().of_cell[index]
    assert expected is not None
    assert cells.neighbourhood_at("Soho") == sample_neighbourhoods().listing[expected]


def test_a_bundle_without_neighbourhoods_has_none(tmp_path):
    from atlas.publish.bundle import Neighbourhoods

    empty = Neighbourhoods(listing=[], of_cell=[None] * len(CELLS), datasets=[])
    cells = read_cells(write_sample(tmp_path, neighbourhoods=empty), PLACES)
    assert cells.neighbourhood_at("Soho") is None


def test_each_column_is_described_by_its_indicator_and_option(cells):
    described = {d.column: d for d in cells.described()}
    ptal = described["service_level"]
    assert ptal.indicator == "service-level" and ptal.unit == "PTAL band"
    assert ptal.curve is not None and ptal.curve.shape == "lookup" and ptal.option is None
    sikh = described["faith__sikh"]
    assert sikh.indicator == "faith" and sikh.unit == "minutes on foot"
    assert sikh.option is not None and sikh.option.name == "Sikh"
    assert sikh.datasets == ["openstreetmap"]
