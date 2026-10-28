import h3
import numpy as np
import pandas as pd
import pytest

from atlas.indicators import amenities
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import SPEED, Network

SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)


def place_table(x: float, y: float) -> pd.DataFrame:
    return pd.DataFrame({"Easting": [x], "Northing": [y], "name": ["A"], "cuisine": [None]})


def street_through_soho() -> tuple[Network, float, float]:
    x, y = cell_centres_bng([SOHO])[0]
    street = [(i, x - 400 + 80.0 * i, y) for i in range(11)]  # a node every 80 m
    return Network.from_ways([street]), x, y


class TestNearestMinutes:
    def test_each_kind_has_the_minutes_to_its_nearest_place(self):
        network, x, y = street_through_soho()
        found = {
            "grocery": place_table(x + 160, y),
            "pharmacy": place_table(x + 320, y),
            "gym": place_table(x - 400, y),
            "library": place_table(x + 400, y),
        }
        minutes = amenities.nearest_minutes(network, found, [SOHO])
        assert set(minutes) == {"groceries", "pharmacies", "gyms", "libraries"}
        assert minutes["groceries"][SOHO] == pytest.approx(160 / SPEED, abs=0.2)
        assert minutes["pharmacies"][SOHO] == pytest.approx(320 / SPEED, abs=0.2)
        assert minutes["gyms"][SOHO] == pytest.approx(400 / SPEED, abs=0.2)

    def test_a_kind_with_no_place_gives_no_value(self):
        network, x, y = street_through_soho()
        minutes = amenities.nearest_minutes(network, {"grocery": place_table(x, y)}, [SOHO])
        assert np.isnan(minutes["libraries"][SOHO]) and np.isfinite(minutes["groceries"][SOHO])
