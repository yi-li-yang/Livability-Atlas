import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import gpps
from atlas.indicators.health import patient_rating

HEADER = "ad_practicecode,ad_practicename,overallexp.pcteval,overallexp.baseevaluw,other.pcteval\n"


def write(tmp_path, rows: str):
    path = tmp_path / "practice.csv"
    path.write_text(HEADER + rows, encoding="utf-8")
    return path


class TestReadRatings:
    def test_it_reads_each_practice_share_rating_its_experience_good(self, tmp_path):
        path = write(tmp_path, "A84002,One,.931,113,.5\nB81001,Two,.75,240,.2\n")
        ratings = gpps.read_ratings(path)
        assert ratings.index.tolist() == ["A84002", "B81001"]
        assert ratings["good"].tolist() == [pytest.approx(0.931), pytest.approx(0.75)]
        assert ratings["answers"].tolist() == [113, 240]

    def test_a_suppressed_result_has_no_value_and_a_tiny_one_is_near_0(self, tmp_path):
        path = write(tmp_path, "A1,One,-97,6,0\nA2,Two,-98,30,0\nA3,Three,,0,0\n")
        ratings = gpps.read_ratings(path)
        assert np.isnan(ratings.loc["A1", "good"])
        assert ratings.loc["A2", "good"] == pytest.approx(0.0025)
        assert np.isnan(ratings.loc["A3", "good"])

    def test_a_file_without_the_column_is_refused(self, tmp_path):
        path = tmp_path / "practice.csv"
        path.write_text("ad_practicecode,something\nA1,1\n", encoding="utf-8")
        with pytest.raises(ValueError, match=r"overallexp\.pcteval"):
            gpps.read_ratings(path)


CELLS = [h3.latlng_to_cell(51.5, -0.1, 9), h3.latlng_to_cell(51.6, -0.2, 9)]


class FakeNetwork:
    """The first cell reaches practices 0 and 1, the second none."""

    def places_within(self, places, origins, minutes):
        self.minutes = minutes
        return [np.array([0, 1]), np.array([], dtype=int)]


class TestPatientRating:
    def test_it_is_the_rating_of_the_practices_in_reach_weighted_by_their_patients(self):
        network = FakeNetwork()
        rating = patient_rating(
            network,  # type: ignore[arg-type]
            np.zeros((2, 2)),
            np.array([0.9, 0.6]),
            np.array([3000.0, 1000.0]),
            CELLS,
        )
        assert rating.iloc[0] == pytest.approx((0.9 * 3000 + 0.6 * 1000) / 4000 * 100)
        assert np.isnan(rating.iloc[1])
        assert network.minutes == 15

    def test_a_practice_with_no_rating_is_left_out_of_the_mean(self):
        rating = patient_rating(
            FakeNetwork(),  # type: ignore[arg-type]
            np.zeros((2, 2)),
            np.array([0.8, np.nan]),
            np.array([1000.0, 5000.0]),
            CELLS,
        )
        assert rating.iloc[0] == pytest.approx(80.0)

    def test_no_rated_practice_in_reach_gives_no_value(self):
        rating = patient_rating(
            FakeNetwork(),  # type: ignore[arg-type]
            np.zeros((2, 2)),
            np.array([np.nan, np.nan]),
            np.array([1000.0, 5000.0]),
            CELLS,
        )
        assert rating.isna().all()
        assert isinstance(rating, pd.Series)


def test_the_family_joins_the_survey_to_the_practices_by_their_code(monkeypatch, tmp_path):
    from atlas.datasets.countries.gb import nhs_gp
    from atlas.families import Context, gp_experience
    from atlas.indicators import health

    practices = pd.DataFrame(
        {"Postcode": ["X", "Y"], "patients": [3000.0, 1000.0], "gps": [2.0, 1.0]},
        index=pd.Index(["A1", "A2"], name="code"),
    )
    monkeypatch.setattr(nhs_gp, "fetch", lambda d: (tmp_path, tmp_path))
    monkeypatch.setattr(nhs_gp, "read_practices", lambda a, b: practices)
    monkeypatch.setattr(
        health, "located_practices", lambda p, c: p.assign(Easting=0.0, Northing=0.0)
    )
    monkeypatch.setattr(gpps, "fetch", lambda d: tmp_path)
    monkeypatch.setattr(
        gpps,
        "read_ratings",
        lambda p: pd.DataFrame({"good": [0.6, 0.9, 0.1]}, index=["A2", "A1", "ZZ"]),
    )
    ctx = Context("london", None, CELLS, tmp_path, pd.DataFrame(), FakeNetwork())  # type: ignore[arg-type]
    values = gp_experience.columns(ctx)["gp-experience"]
    assert values[0] == pytest.approx((0.9 * 3000 + 0.6 * 1000) / 4000 * 100)
    assert values[1] is None
    assert gp_experience.FAMILY.built_from == {"gp-experience": ("nhs-gp-patient-survey",)}
