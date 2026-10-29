from collections.abc import Sequence

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.indicators import faith
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import SPEED, Network


def osm(rows: Sequence[tuple[str, str | None, float, float]]) -> pd.DataFrame:
    """OpenStreetMap places at longitude -0.12, latitude 51.51 plus the offsets given; the rows
    are (amenity, religion, metres east, metres north)."""
    return pd.DataFrame(
        {
            "amenity": [r[0] for r in rows],
            "religion": [r[1] for r in rows],
            "lng": [-0.12 + r[2] / 69000 for r in rows],
            "lat": [51.51 + r[3] / 111000 for r in rows],
        }
    )


class TestPlacesOfWorship:
    def test_places_are_grouped_by_the_religion_they_record(self):
        frame = osm(
            [("place_of_worship", "hindu", 0, 0)] * 12
            + [("place_of_worship", "muslim", 100, 0)] * 12
            + [("cafe", None, 0, 0)]
        )
        found = faith.places_of_worship(frame, minimum=10)
        assert sorted(found) == ["hindu", "muslim"]
        assert found["hindu"].shape == (12, 2)

    def test_a_religion_with_too_few_places_is_left_out(self):
        frame = osm(
            [("place_of_worship", "sikh", 0, 0)] * 9 + [("place_of_worship", "jewish", 0, 0)] * 10
        )
        assert list(faith.places_of_worship(frame, minimum=10)) == ["jewish"]

    def test_a_multifaith_place_is_not_a_faith_to_pick(self):
        frame = osm([("place_of_worship", "multifaith", 0, 0)] * 12)
        assert faith.places_of_worship(frame, minimum=10) == {}

    def test_a_place_with_no_religion_or_several_is_handled(self):
        frame = osm(
            [("place_of_worship", None, 0, 0)] * 10
            + [("place_of_worship", "christian;muslim", 0, 0)] * 10
        )
        found = faith.places_of_worship(frame, minimum=10)
        assert sorted(found) == ["christian", "muslim"]  # a shared place counts for each

    def test_the_picker_names_a_religion_in_plain_words(self):
        assert faith.name_of("hindu") == "Hindu"
        assert faith.name_of("bahai") == "Bahai"


class TestMinutes:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def test_it_is_the_walk_to_the_nearest_place_of_the_religion(self):
        x, y = cell_centres_bng([self.cell])[0]
        street = [(i, x - 400 + 80.0 * i, y) for i in range(31)]
        network = Network.from_ways([street])
        places = {"hindu": np.array([[x + 240, y]]), "sikh": np.array([[x + 800, y]])}
        minutes = faith.faith_minutes(network, places, [self.cell])
        assert minutes["hindu"][self.cell] == pytest.approx(240 / SPEED, abs=0.2)
        assert minutes["sikh"][self.cell] == pytest.approx(800 / SPEED, abs=0.2)
