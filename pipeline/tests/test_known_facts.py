"""Facts about London that the built data must agree with.

These read the real bundle that `just data london` builds, so they are skipped where there is none,
as in CI. Run `just data london` and then `just check` to run them.
"""

import json

import h3
import pandas as pd
import pytest

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
    crime = [c for c in bundle.columns if c != "service_level"]
    assert len(crime) == 5
    assert bundle[crime].notna().all().all()


def test_rates_are_per_1000_residents_so_they_are_of_a_plausible_size(bundle):
    # London records about 1 burglary per 200 residents a year: a median near 5 per 1,000.
    assert 2 < bundle["burglary"].median() < 12
    assert 10 < bundle["violence_and_sexual_offences"].median() < 60


def test_the_city_of_london_tops_the_rates_because_of_its_workers_not_residents(bundle):
    """Spike S2's known limit: workers and visitors are in the counts, but not in the residents."""
    assert bundle.loc[BANK, "burglary"] > bundle["burglary"].quantile(0.99)
