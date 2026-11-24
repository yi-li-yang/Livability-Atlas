"""The travel estimate to a user's place reproduces the golden cases of shared/fixtures/travel/."""

import json
import math

import pytest

from atlas.paths import REPO_ROOT
from atlas.scoring.travel import estimate, straight_metres

FIXTURES = sorted((REPO_ROOT / "shared" / "fixtures" / "travel").glob("*.json"))


def test_there_are_golden_cases():
    assert len(FIXTURES) >= 4


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_the_estimate_reproduces_each_golden_case(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    got = estimate(case)
    if case["expected"] is None:
        assert got is None
    else:
        assert got is not None
        assert math.isclose(got, case["expected"], abs_tol=1e-9)


def test_a_straight_line_along_a_meridian_is_the_radius_times_the_angle():
    assert math.isclose(straight_metres(51.0, 0.0, 51.001, 0.0), 111.19508023353292, abs_tol=1e-9)
    # across: a degree of longitude at 60 degrees north is about half a degree of latitude
    across = straight_metres(60.0, 0.0, 60.0, 1.0)
    assert 55_500 < across < 55_700


def region(case: dict, with_place_cell: bool = True):
    """The case as a region of two cells: the case's cell, and the cell that holds the place, with
    the place's links when it has them."""
    import numpy as np

    from atlas.scoring.travel import region_minutes

    cell, place = case["cell"], case["place"]
    links = [(0, s, m) for s, m in cell["stations"]]
    links += [(1, s, m) for s, m in place.get("stations", [])]
    has_cell = with_place_cell and "stations" in place
    return region_minutes(
        np.array(case["stations"], dtype=float),
        np.array(case["matrix"], dtype=np.uint16),
        np.array(links, dtype=float).reshape(-1, 3),
        np.array([[cell["lat"], cell["lng"]], [place["lat"], place["lng"]]]),
        (place["lat"], place["lng"]),
        case["constants"],
        place_cell=1 if has_cell else None,
    )[0]


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_the_region_estimate_gives_each_cell_the_one_cell_estimate(path):
    case = json.loads(path.read_text(encoding="utf-8"))
    got = region(case)
    if case["expected"] is None:
        assert math.isnan(got)
    else:
        assert math.isclose(got, case["expected"], abs_tol=1e-9)


def test_a_place_outside_the_cells_keeps_the_straight_walk():
    # The same case with no cell for the place: no station is within a walk of it.
    case = json.loads(
        (REPO_ROOT / "shared" / "fixtures" / "travel" / "bus-at-the-far-end.json").read_text(
            encoding="utf-8"
        )
    )
    assert math.isnan(region(case, with_place_cell=False))
    del case["place"]["stations"]
    assert estimate(case) is None
