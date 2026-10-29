import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import fsa
from atlas.indicators import amenities
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)


class Reply:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def establishment(name: str, rating: str, lng="-0.13", lat="51.51") -> dict:
    return {
        "BusinessName": name,
        "BusinessType": "Restaurant/Cafe/Canteen",
        "RatingValue": rating,
        "geocode": {"longitude": lng, "latitude": lat},
    }


class TestFetch:
    def fake_get(self, calls):
        def get(url, headers, timeout, params=None):
            calls.append((url, params))
            if url.endswith("/Authorities"):
                return Reply(
                    {
                        "authorities": [
                            {"LocalAuthorityId": 1, "Name": "Camden", "RegionName": "London"},
                            {"LocalAuthorityId": 2, "Name": "Leeds", "RegionName": "Yorkshire"},
                        ]
                    }
                )
            return Reply(
                {
                    "establishments": [
                        establishment("Good Cafe", "5"),
                        establishment("Waiting", "AwaitingInspection"),
                        {"BusinessName": "No place", "RatingValue": "4", "geocode": None},
                        establishment("Odd place", "3", lng="", lat=""),
                    ]
                }
            )

        return get

    def test_keeps_the_rated_businesses_with_a_place_of_the_regions_authorities(
        self, tmp_path, monkeypatch
    ):
        calls = []
        monkeypatch.setattr(fsa.requests, "get", self.fake_get(calls))
        path = fsa.fetch(tmp_path, "london")
        businesses = fsa.read_ratings(path)
        assert businesses["rating"].tolist() == [5]
        assert [p["localAuthorityId"] for _, p in calls if p] == [1]  # Leeds is not London

    def test_businesses_awaiting_inspection_and_other_schemes_are_not_rated(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(fsa.requests, "get", self.fake_get([]))
        businesses = fsa.read_ratings(fsa.fetch(tmp_path, "london"))
        assert businesses["rating"].tolist() == [5]
        assert businesses["lng"].tolist() == [-0.13]

    def test_the_file_is_fetched_once(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(fsa.requests, "get", self.fake_get(calls))
        fsa.fetch(tmp_path, "london")
        first = len(calls)
        fsa.fetch(tmp_path, "london")
        assert len(calls) == first


def street_through_soho() -> tuple[Network, float, float]:
    x, y = cell_centres_bng([SOHO])[0]
    return Network.from_ways([[(i, x - 400 + 80.0 * i, y) for i in range(11)]]), x, y


def ratings(x: float, y: float, values: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Easting": [x + 10 * i for i in range(len(values))],
            "Northing": [y] * len(values),
            "rating": values,
        }
    )


class TestShareRatedGood:
    def test_it_is_the_percentage_of_rated_businesses_in_reach_that_are_good(self):
        network, x, y = street_through_soho()
        values = [5, 5, 4, 4, 3, 2, 1, 0, 5, 3]  # 5 of 10 are 4 or 5
        share = amenities.good_hygiene_share(network, ratings(x, y, values), [SOHO])
        assert share[SOHO] == pytest.approx(50.0)

    def test_a_cell_with_too_few_rated_businesses_has_no_value(self):
        network, x, y = street_through_soho()
        share = amenities.good_hygiene_share(network, ratings(x, y, [5, 5, 5, 5]), [SOHO])
        assert np.isnan(share[SOHO])

    def test_businesses_beyond_the_walk_do_not_count(self):
        x, y = cell_centres_bng([SOHO])[0]
        long_street = Network.from_ways([[(i, x - 80.0 + 80.0 * i, y) for i in range(25)]])
        near = ratings(x, y, [5] * 5)
        far = ratings(x + 1500, y, [0] * 20)
        share = amenities.good_hygiene_share(long_street, pd.concat([near, far]), [SOHO])
        assert share[SOHO] == pytest.approx(100.0)
