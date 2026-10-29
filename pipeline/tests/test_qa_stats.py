import numpy as np
import pytest

from atlas.catalogue.models import IdealRange, Percentile, Ramp
from atlas.publish.bundle import Choice
from atlas.qa.cells import read_cells
from atlas.qa.stats import column_stats, curve_span, factor_coverage
from atlas.scoring.engine import curve_score
from tests.qa_sample import spoil, write_sample


def stats_of(folder):
    return {s.column: s for s in column_stats(read_cells(folder))}


@pytest.fixture
def stats(tmp_path):
    return stats_of(write_sample(tmp_path))


def test_a_number_column_has_its_range_and_its_percentiles(stats):
    minutes = stats["station_proximity"]
    assert (minutes.indicator, minutes.unit, minutes.option) == (
        "station-proximity",
        "minutes on foot",
        None,
    )
    assert minutes.valued == 1.0
    assert (minutes.lowest, minutes.median, minutes.highest) == (2.0, 8.0, 30.0)
    assert minutes.p5 == pytest.approx(2.0 + 0.3 * 1.5)  # the 5th percentile, interpolated
    assert minutes.p95 == pytest.approx(15.0 + 0.7 * 15.0)
    assert minutes.categories is None


def test_cells_without_a_value_are_left_out_of_the_percentiles(tmp_path):
    folder = write_sample(tmp_path, columns={"station-proximity": [2, None, 5, 8, 12, 15, None]})
    minutes = stats_of(folder)["station_proximity"]
    assert minutes.valued == pytest.approx(5 / 7)
    assert (minutes.lowest, minutes.median, minutes.highest) == (2.0, 8.0, 15.0)


def test_a_column_with_no_value_has_no_percentiles(tmp_path):
    folder = write_sample(tmp_path, columns={"diversity": [None] * 7})
    diversity = stats_of(folder)["diversity"]
    assert diversity.valued == 0.0
    assert diversity.lowest is None and diversity.median is None and diversity.highest is None


def test_a_ramp_shows_how_many_cells_are_at_full_marks_and_at_none(stats):
    # The ramp is 25 minutes for no marks and 6 for full marks: three cells are within 6 minutes
    # and one is beyond 25.
    minutes = stats["station_proximity"]
    assert minutes.full == pytest.approx(3 / 7)
    assert minutes.none == pytest.approx(1 / 7)


def test_the_share_at_full_marks_is_of_the_cells_with_a_value(tmp_path):
    folder = write_sample(tmp_path, columns={"station-proximity": [2, 3.5, None, None, 12, 15, 30]})
    minutes = stats_of(folder)["station_proximity"]
    assert minutes.full == pytest.approx(2 / 5) and minutes.none == pytest.approx(1 / 5)


CURVES = [
    Ramp(shape="ramp", t0=25, t1=6),  # lower is better
    Ramp(shape="ramp", t0=0, t1=100),  # higher is better
    IdealRange(shape="ideal-range", l0=10, l1=18, u1=24, u0=32),
]


@pytest.mark.parametrize("curve", CURVES, ids=lambda c: c.shape + str(c.model_dump()))
def test_the_share_at_full_marks_and_at_none_is_what_the_reference_scorer_gives(curve):
    values = np.concatenate(
        [np.random.default_rng(1).uniform(-20, 140, 500), [-5.0, 0.0, 6.0, 10.0, 25.0, 100.0]]
    )
    scores = [curve_score(curve.model_dump(), float(v)) for v in values]
    scored = [s for s in scores if s is not None]
    assert len(scored) == len(values)  # a ramp and an ideal range score every value
    expected = (np.mean([s >= 1.0 for s in scored]), np.mean([s <= 0.0 for s in scored]))
    assert curve_span(curve, values) == pytest.approx(expected)


def test_a_curve_that_is_not_a_ramp_or_an_ideal_range_has_no_span():
    assert curve_span(Percentile(shape="percentile", better="higher"), np.array([1.0, 2.0])) == (
        None,
        None,
    )
    assert curve_span(None, np.array([1.0, 2.0])) == (None, None)


def test_a_percentile_curve_has_no_full_or_none(stats):
    assert stats["diversity"].full is None and stats["diversity"].none is None


def test_an_option_is_scored_by_its_indicators_curve(stats):
    hindu = stats["faith__hindu"]
    assert hindu.option == "Hindu" and hindu.indicator == "faith"
    # The ramp is 15 minutes for no marks and 5 for full marks, and every walk is 20 or more.
    assert hindu.full == 0.0 and hindu.none == 1.0
    assert stats["faith__sikh"].none == pytest.approx(4 / 7)  # the walks of 15 minutes or more
    assert stats["faith__sikh"].full == 0.0


def test_a_text_column_has_the_share_of_cells_in_each_category_with_its_score(stats):
    ptal = stats["service_level"]
    assert ptal.lowest is None and ptal.median is None
    assert ptal.valued == 1.0
    shares = {c.value: (c.share, c.score) for c in ptal.categories or ()}
    assert shares["6b"] == (pytest.approx(1 / 7), 1.0)
    assert shares["1b"] == (pytest.approx(1 / 7), 0.25)
    order = [c.value for c in ptal.categories or ()]
    assert order == ["1b", "2", "3", "4", "5", "6a", "6b"]  # the curve's order, worst to best


def test_a_text_column_counts_the_cells_without_a_value_apart(tmp_path):
    folder = write_sample(
        tmp_path, columns={"service-level": ["6b", None, "5", "4", "3", "2", "1b"]}
    )
    ptal = stats_of(folder)["service_level"]
    assert ptal.valued == pytest.approx(6 / 7)
    assert sum(c.share for c in ptal.categories or ()) == pytest.approx(6 / 7)


def test_a_factor_is_covered_by_the_share_of_its_indicators_that_a_cell_has(tmp_path):
    folder = write_sample(tmp_path, columns={"station-proximity": [2, None, 5, 8, 12, 15, 30]})
    transport = {f.id: f for f in factor_coverage(read_cells(folder))}["transport"]
    assert transport.indicators == 2
    assert transport.mean == pytest.approx(13 / 14)  # one cell has one of the two indicators
    assert transport.unscored == 0.0
    assert transport.low == pytest.approx(1 / 7)  # that cell has 50%, under the 70% flag


def test_a_cell_exactly_at_the_flag_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr("atlas.qa.stats.LOW_COVERAGE", 0.5)
    folder = write_sample(tmp_path, columns={"station-proximity": [2, None, 5, 8, 12, 15, 30]})
    transport = {f.id: f for f in factor_coverage(read_cells(folder))}["transport"]
    assert transport.low == 0.0  # the cell with one of two indicators has exactly 50%


def test_a_cell_with_none_of_a_factors_indicators_cannot_be_scored_for_it(tmp_path):
    folder = write_sample(
        tmp_path,
        columns={
            "station-proximity": [None, 3.5, 5, 8, 12, 15, 30],
            "service-level": [None, "6a", "5", "4", "3", "2", "1b"],
        },
    )
    transport = {f.id: f for f in factor_coverage(read_cells(folder))}["transport"]
    assert transport.unscored == pytest.approx(1 / 7)
    assert transport.mean == pytest.approx(6 / 7)


def test_a_choice_indicator_counts_when_any_of_its_options_has_a_value(tmp_path):
    folder = write_sample(tmp_path, columns={"diversity": [None] * 7})
    community = {f.id: f for f in factor_coverage(read_cells(folder))}["community-and-people"]
    assert community.indicators == 2
    assert community.mean == pytest.approx(0.5)  # faith has values, diversity has none
    assert community.low == 1.0


def test_a_choice_indicator_with_one_option_that_has_values_still_counts(tmp_path):
    options = [
        Choice("hindu", "Hindu", None, [None] * 7),  # no cell has a value for this option
        Choice("sikh", "Sikh", None, [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]),
    ]
    folder = write_sample(tmp_path, choices={"faith": options})
    community = {f.id: f for f in factor_coverage(read_cells(folder))}["community-and-people"]
    assert community.mean == pytest.approx(1.0) and community.low == 0.0


def test_the_factors_are_listed_in_the_manifests_order(tmp_path):
    cells = read_cells(write_sample(tmp_path))
    assert [f.id for f in factor_coverage(cells)] == [f.id for f in cells.manifest.factors]
    assert factor_coverage(cells)[0].name == cells.manifest.factors[0].name


def test_stats_follow_the_manifests_columns_in_order(tmp_path):
    folder = spoil(write_sample(tmp_path))
    cells = read_cells(folder)
    assert [s.column for s in column_stats(cells)] == [d.column for d in cells.described()]
