import json

import h3
import numpy as np
import pytest

from atlas.datasets.cities.london import planning_datahub
from atlas.indicators import regeneration
from atlas.spatial.grid import cell_centres_bng


def unit(change: str, completed: str | None) -> dict:
    return {"change_type": change, "actual_completion_date": completed}


def scheme(
    units: list[dict], completed: str = "17/11/2022", x: int | None = 530000, y: int | None = 180000
) -> dict:
    return {
        "id": "Borough-1",
        "actual_completion_date": completed,
        "centroid_easting": x,
        "centroid_northing": y,
        "application_details": {"residential_details": {"residential_units": units}},
    }


class TestHomes:
    def test_it_counts_the_homes_gained_and_lost_in_the_window(self):
        found = planning_datahub.homes(
            scheme([unit("Gain", "01/05/2021"), unit("gain", None), unit("Loss", "01/05/2021")])
        )
        # A home with no date of its own takes the scheme's; "gain" in lower case still counts.
        assert found == {"id": "Borough-1", "x": 530000.0, "y": 180000.0, "gained": 2, "lost": 1}

    def test_a_home_completed_outside_the_window_is_not_counted(self):
        found = planning_datahub.homes(
            scheme(
                [unit("Gain", "01/05/2019"), unit("Gain", "01/05/2025"), unit("Gain", "31/03/2025")]
            )
        )
        assert found is not None and found["gained"] == 1

    def test_a_scheme_with_no_place_is_left_out(self):
        assert planning_datahub.homes(scheme([unit("Gain", None)], x=None, y=None)) is None


def test_kept_schemes_are_read_back(tmp_path):
    path = tmp_path / "completions.json"
    rows = [{"id": "A", "x": 1.0, "y": 2.0, "gained": 3, "lost": 0}]
    path.write_text(json.dumps(rows), encoding="utf-8")
    table = planning_datahub.read_completions(path)
    assert table["gained"].tolist() == [3]


CELL = h3.latlng_to_cell(51.5, -0.1, 9)


def test_the_homes_within_a_radius_are_summed():
    x, y = cell_centres_bng([CELL])[0]
    points = np.array([[x + 100, y], [x + 999, y], [x + 1500, y]])
    total = regeneration.sum_within(points, np.array([10.0, 5.0, 100.0]), [CELL], 1000.0)
    assert total.tolist() == [pytest.approx(15.0)]


def test_no_scheme_gives_0():
    assert regeneration.sum_within(np.zeros((0, 2)), np.zeros(0), [CELL], 1000.0).tolist() == [0.0]
