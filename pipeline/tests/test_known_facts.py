"""Facts about London that the built data must agree with.

These read the real bundle that `just data london` builds, so they are skipped where there is none,
as in CI. Run `just data london` and then `just check` to run them.
"""

import json

import h3
import pandas as pd
import pytest

from atlas.indicators.crime import CATEGORIES
from atlas.paths import data_dir

LONDON = data_dir() / "published" / "london"
pytestmark = pytest.mark.skipif(
    not (LONDON / "latest.json").exists(), reason="no built London bundle: run `just data london`"
)


def cell_at(lat: float, lng: float) -> str:
    return h3.latlng_to_cell(lat, lng, 9)


@pytest.fixture(scope="module")
def bundle() -> pd.DataFrame:
    version = json.loads((LONDON / "latest.json").read_text(encoding="utf-8"))["version"]
    return pd.read_parquet(LONDON / version / "cells.parquet").set_index("cell")


SOHO = cell_at(51.5136, -0.1337)
WIMBLEDON_VILLAGE = cell_at(51.4214, -0.2056)
BANK = cell_at(51.5133, -0.0890)


@pytest.mark.parametrize(
    "column",
    [
        "burglary",
        "violence_and_sexual_offences",
        "robbery_and_theft_from_the_person",
        "anti_social_behaviour",
    ],
)
def test_soho_has_more_crime_per_resident_than_wimbledon_village(bundle, column):
    assert bundle.loc[SOHO, column] > 3 * bundle.loc[WIMBLEDON_VILLAGE, column]


def test_every_cell_has_a_rate_for_each_crime_indicator(bundle):
    columns = [name.replace("-", "_") for name in CATEGORIES]
    assert len(columns) == 5
    assert bundle[columns].notna().all().all()


def test_rates_are_per_1000_residents_so_they_are_of_a_plausible_size(bundle):
    # London records about 1 burglary per 200 residents a year: a median near 5 per 1,000.
    assert 2 < bundle["burglary"].median() < 12
    assert 10 < bundle["violence_and_sexual_offences"].median() < 60


def test_the_city_of_london_tops_the_rates_because_of_its_workers_not_residents(bundle):
    """Spike S2's known limit: workers and visitors are in the counts, but not in the residents."""
    assert bundle.loc[BANK, "burglary"] > bundle["burglary"].quantile(0.99)


HACKNEY_MARSHES = cell_at(51.5530, -0.0290)  # the Lea valley floodplain
CRYSTAL_PALACE_HILL = cell_at(51.4190, -0.0750)


def test_flood_shares_are_percentages_of_the_area_and_mostly_zero(bundle):
    for column in ("river_and_sea_flooding", "surface_water_flooding"):
        assert bundle[column].notna().all()
        assert bundle[column].between(0, 100).all()
        assert bundle[column].median() == 0  # most of London is not at risk of 1 in 100


def test_the_lea_valley_floodplain_is_more_at_risk_from_rivers_than_a_hilltop(bundle):
    assert bundle.loc[HACKNEY_MARSHES, "river_and_sea_flooding"] > 20
    assert bundle.loc[CRYSTAL_PALACE_HILL, "river_and_sea_flooding"] == 0


CHINGFORD = cell_at(51.6330, -0.0100)


def test_every_cell_has_a_walk_to_a_station_and_the_centre_is_better_served(bundle):
    minutes = bundle["station_proximity"]
    assert minutes.notna().all()
    assert minutes.min() >= 0
    assert minutes.loc[BANK] < 6 < minutes.loc[CHINGFORD]
    assert minutes.loc[SOHO] < 8


def test_most_of_london_is_within_a_30_minute_walk_of_a_station(bundle):
    minutes = bundle["station_proximity"]
    assert 8 < minutes.median() < 25
    assert (minutes <= 30).mean() > 0.75
