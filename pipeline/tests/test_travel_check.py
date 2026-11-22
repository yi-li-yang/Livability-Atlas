"""The comparison of the travel estimate with the Journey Planner."""

import math

import numpy as np

from atlas.travel_check import errors, sample_pairs, table


def test_the_sample_is_the_same_each_time_and_never_pairs_a_cell_with_itself():
    a = sample_pairs(50, 10)
    assert a == sample_pairs(50, 10)
    assert len(a) == 50
    assert all(x != y and 0 <= x < 10 and 0 <= y < 10 for x, y in a)


def test_the_errors_are_the_estimate_less_the_time_overall_and_by_length():
    estimate = np.array([12.0, 30.0, 55.0, np.nan])
    journey = np.array([10.0, 40.0, 50.0, 20.0])
    metres = np.array([1_000.0, 8_000.0, 20_000.0, 3_000.0])
    rows = errors(estimate, journey, metres)
    overall = rows[0]
    assert overall.journeys == 3
    assert overall.median_error == 2.0  # +2, -10, +5
    assert math.isclose(overall.mean_absolute, (2 + 10 + 5) / 3)
    assert math.isclose(overall.within_20, 2 / 3)  # 20% and 10% are within; 25% is not
    assert [r.journeys for r in rows[1:]] == [1, 1, 1]


def test_the_table_has_a_row_for_each_group():
    rows = errors(np.array([10.0]), np.array([10.0]), np.array([100.0]), "08:30")
    text = table(rows)
    assert "| 08:30 | 1 | +0.0 min | 0.0 min | 100% |" in text
    assert "| 08:30, over 15 km | 0 |" in text
