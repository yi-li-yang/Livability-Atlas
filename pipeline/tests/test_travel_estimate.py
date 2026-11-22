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


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_the_region_estimate_gives_each_cell_the_one_cell_estimate(path):
    import numpy as np

    from atlas.scoring.travel import region_minutes

    case = json.loads(path.read_text(encoding="utf-8"))
    cell = case["cell"]
    got = region_minutes(
        np.array(case["stations"], dtype=float),
        np.array(case["matrix"], dtype=np.uint16),
        np.array([(0, s, m) for s, m in cell["stations"]], dtype=float).reshape(-1, 3),
        np.array([[cell["lat"], cell["lng"]]]),
        (case["place"]["lat"], case["place"]["lng"]),
        case["constants"],
    )[0]
    if case["expected"] is None:
        assert math.isnan(got)
    else:
        assert math.isclose(got, case["expected"], abs_tol=1e-9)
