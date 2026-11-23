import math

import pytest

from atlas.catalogue.models import RegionRamp
from atlas.publish.curves import region_ends, resolve


def borough_like(values_and_cells):
    """Each value repeated for its number of cells, as a value per borough gives."""
    return [v for v, n in values_and_cells for _ in range(n)]


def test_whole_areas_are_kept_at_both_ends():
    # The dearest area holds under 1% of the cells, but it is a whole area, so it is not cut.
    values = borough_like([(3739, 90), (3209, 200), (2000, 9000), (1540, 2000)])
    assert region_ends(values) == (1540, 3739)


def test_the_most_extreme_cells_are_left_out_up_to_one_in_a_hundred():
    values = list(range(10_000))  # every value in one cell only
    assert region_ends(values) == (100, 9899)


def test_a_count_keeps_none_as_its_low_end():
    # Most cells have none, and a few have very many.
    values = [0] * 8000 + list(range(1, 2001)) + [5000, 6000]
    ends = region_ends(values)
    assert ends is not None
    low, high = ends
    assert low == 0
    assert high < 5000


def test_missing_values_are_ignored():
    assert region_ends([None, 1.0, float("nan"), 2.0]) == (1.0, 2.0)
    assert region_ends([None, float("nan")]) is None


def test_a_falling_region_ramp_scores_the_lowest_value_best():
    ramp = resolve(RegionRamp(shape="region-ramp", better="lower", log=True), [1540, 3739, 2000])
    assert ramp is not None
    assert (ramp.t0, ramp.t1, ramp.log, ramp.offset, ramp.from_region) == (
        3739,
        1540,
        True,
        None,
        True,
    )


def test_a_rising_count_ramp_keeps_its_offset():
    curve = RegionRamp(shape="region-ramp", better="higher", log=True, offset=1)
    ramp = resolve(curve, [0, 0, 3, 10])
    assert ramp is not None
    assert (ramp.t0, ramp.t1, ramp.offset) == (0, 10, 1)


def test_a_linear_region_ramp_has_no_log():
    ramp = resolve(RegionRamp(shape="region-ramp", better="higher"), [0.2, 0.9])
    assert ramp is not None
    assert ramp.log is None and ramp.offset is None


def test_a_single_value_gives_no_curve():
    # The indicator cannot tell this region's cells apart.
    assert resolve(RegionRamp(shape="region-ramp", better="lower"), [7, 7, 7]) is None
    assert resolve(RegionRamp(shape="region-ramp", better="lower"), []) is None


def test_a_log_ramp_without_an_offset_starts_above_zero():
    # A value of 0 cannot be on a log scale with no offset, so the low end is the lowest value
    # above 0, and a 0 scores as that end.
    ramp = resolve(RegionRamp(shape="region-ramp", better="higher", log=True), [0, 2, 4, 8])
    assert ramp is not None
    assert (ramp.t0, ramp.t1) == (2, 8)


def test_a_log_ramp_without_an_offset_trims_its_values_above_zero():
    # Zeros cannot be on the scale, and one tiny rate must not set the end that scores 1: the
    # trim applies to the values above 0, as to any others.
    values = [0.0] * 5000 + [0.003] + [1.0 + i / 100 for i in range(3000)]
    ramp = resolve(RegionRamp(shape="region-ramp", better="lower", log=True), values)
    assert ramp is not None
    assert ramp.t1 > 1.0  # not 0.003


@pytest.mark.parametrize("values", [[0, 0], [-1, 0]])
def test_a_log_ramp_with_nothing_above_zero_gives_no_curve(values):
    assert resolve(RegionRamp(shape="region-ramp", better="higher", log=True), values) is None


def test_the_ends_are_plain_numbers():
    ramp = resolve(RegionRamp(shape="region-ramp", better="lower"), [1, 2, 3])
    assert ramp is not None
    assert isinstance(ramp.t0, float) and not math.isnan(ramp.t0)
