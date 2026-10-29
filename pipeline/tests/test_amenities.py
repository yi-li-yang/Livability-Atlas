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


def table(*rows: tuple) -> pd.DataFrame:
    """Places as (easting, northing, cuisine)."""
    return pd.DataFrame(
        {
            "Easting": [r[0] for r in rows],
            "Northing": [r[1] for r in rows],
            "name": ["A"] * len(rows),
            "cuisine": [r[2] for r in rows],
        }
    )


class TestCounts:
    def test_cafes_and_restaurants_are_counted_within_ten_minutes_along_the_street(self):
        network, x, y = street_through_soho()  # 400 m each way along the street
        found = {
            "cafe": table((x - 240, y, None), (x + 80, y, None), (x + 400, y, None)),
            "restaurant": table((x, y, None)),
        }
        counts = amenities.counts_within_a_walk(network, found, [SOHO])
        assert counts["cafes"][SOHO] == 3  # all within 480 m of the centre, so 10 minutes
        assert counts["restaurant-choice"][SOHO] == 1

    def test_a_place_beyond_ten_minutes_is_not_counted(self):
        # Streets only 400 m each way here, so put the place on a street 1,000 m away.
        x, y = cell_centres_bng([SOHO])[0]
        long_street = Network.from_ways([[(i, x - 80.0 + 80.0 * i, y) for i in range(20)]])
        found = {"cafe": table((x + 600, y, None), (x + 1200, y, None))}
        counts = amenities.counts_within_a_walk(long_street, found, [SOHO])
        assert counts["cafes"][SOHO] == 1  # 680 m and 1,280 m away along the street

    def test_a_kind_with_no_place_counts_zero(self):
        network, x, y = street_through_soho()
        counts = amenities.counts_within_a_walk(network, {"cafe": table((x, y, None))}, [SOHO])
        assert counts["restaurant-choice"][SOHO] == 0


class TestCuisineVariety:
    def test_it_counts_the_different_cuisines_of_the_restaurants_in_reach(self):
        network, x, y = street_through_soho()
        found = {
            "restaurant": table(
                (x, y, "thai"),
                (x + 80, y, "thai"),  # the same cuisine twice counts once
                (x - 80, y, "indian"),
                (x + 160, y, None),  # no known cuisine counts for none
            )
        }
        assert amenities.cuisine_variety(network, found, [SOHO])[SOHO] == 2

    def test_a_cuisine_beyond_the_walk_does_not_count(self):
        x, y = cell_centres_bng([SOHO])[0]
        long_street = Network.from_ways([[(i, x - 80.0 + 80.0 * i, y) for i in range(20)]])
        found = {"restaurant": table((x, y, "thai"), (x + 1200, y, "greek"))}
        assert amenities.cuisine_variety(long_street, found, [SOHO])[SOHO] == 1

    def test_no_restaurant_in_reach_is_zero_cuisines(self):
        network, x, y = street_through_soho()
        assert amenities.cuisine_variety(network, {}, [SOHO])[SOHO] == 0
