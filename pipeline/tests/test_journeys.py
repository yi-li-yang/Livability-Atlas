import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.cities.london import tfl_journeys
from atlas.indicators import transport
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import SPEED, Network


def journeys(*durations: int) -> dict:
    return {"journeys": [{"duration": d} for d in durations]}


class FakeApi:
    """Answers the Journey Planner from a table of (station, place) -> durations."""

    def __init__(self, answers: dict[tuple[str, str], list[int] | None]):
        self.answers, self.asked = answers, []

    def __call__(self, path: str, missing: bool = False):
        self.asked.append(path)
        origin, destination = path.split("/to/")
        origin = origin.removeprefix("Journey/JourneyResults/")
        destination = destination.split("?")[0]
        found = self.answers.get((origin, destination))
        return None if found is None else journeys(*found)


STATIONS = pd.DataFrame(
    {"stop": ["S1", "S2"], "Latitude": [51.50, 51.60], "Longitude": [-0.10, -0.20]}
)
PLACES = [("Bank", 51.5133, -0.0886), ("King's Cross", 51.5308, -0.1238)]


def answers() -> dict:
    return {
        ("51.5,-0.1", "51.5133,-0.0886"): [25, 31],  # the quickest journey counts
        ("51.5,-0.1", "51.5308,-0.1238"): [20],
        ("51.6,-0.2", "51.5133,-0.0886"): [50],
        ("51.6,-0.2", "51.5308,-0.1238"): None,  # the planner finds no journey
    }


class TestFetch:
    def test_it_keeps_the_quickest_journey_from_each_station_to_each_place(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(tfl_journeys, "_get", FakeApi(answers()))
        monkeypatch.setattr(tfl_journeys, "PAUSE", 0)
        path = tfl_journeys.fetch(tmp_path, "london", STATIONS, PLACES)
        found = tfl_journeys.read_times(path)
        got = {
            (stop, place): minutes
            for stop, place, minutes in found[["stop", "place", "minutes"]].to_numpy()
        }
        assert got[("S1", "Bank")] == 25 and got[("S1", "King's Cross")] == 20
        assert got[("S2", "Bank")] == 50
        assert np.isnan(got[("S2", "King's Cross")])

    def test_it_asks_for_a_weekday_morning(self, tmp_path, monkeypatch):
        api = FakeApi(answers())
        monkeypatch.setattr(tfl_journeys, "_get", api)
        monkeypatch.setattr(tfl_journeys, "PAUSE", 0)
        tfl_journeys.fetch(tmp_path, "london", STATIONS, PLACES)
        assert all("date=20261104" in q and "time=0830" in q for q in api.asked)

    def test_a_stopped_fetch_carries_on_without_asking_again(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tfl_journeys, "PAUSE", 0)
        monkeypatch.setattr(tfl_journeys, "WORKERS", 1)
        first = FakeApi(answers())
        calls = {"n": 0}

        def flaky(path: str, missing: bool = False):
            calls["n"] += 1
            if calls["n"] == 3:
                raise RuntimeError("TfL kept refusing")
            return first(path, missing)

        monkeypatch.setattr(tfl_journeys, "_get", flaky)
        with pytest.raises(RuntimeError):
            tfl_journeys.fetch(tmp_path, "london", STATIONS, PLACES)
        target = tmp_path / "raw" / "tfl" / f"journeys-london-{tfl_journeys.DATE}-0830.csv"
        kept = len(pd.read_csv(target))
        second = FakeApi(answers())
        monkeypatch.setattr(tfl_journeys, "_get", second)
        path = tfl_journeys.fetch(tmp_path, "london", STATIONS, PLACES)
        assert len(second.asked) == 4 - kept  # only the pairs not yet answered
        assert len(tfl_journeys.read_times(path)) == 4

    def test_it_is_fetched_once(self, tmp_path, monkeypatch):
        api = FakeApi(answers())
        monkeypatch.setattr(tfl_journeys, "_get", api)
        monkeypatch.setattr(tfl_journeys, "PAUSE", 0)
        tfl_journeys.fetch(tmp_path, "london", STATIONS, PLACES)
        asked = len(api.asked)
        tfl_journeys.fetch(tmp_path, "london", STATIONS, PLACES)
        assert len(api.asked) == asked


class TestTravelMinutes:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def setup(self):
        x, y = cell_centres_bng([self.cell])[0]
        street = [(i, x - 400 + 80.0 * i, y) for i in range(61)]
        stations = pd.DataFrame(
            {"stop": ["near", "far"], "Easting": [x + 400, x + 1600], "Northing": [y, y]}
        )
        return Network.from_ways([street]), stations

    def times(self, near: tuple[float, float], far: tuple[float, float]) -> pd.DataFrame:
        rows = []
        for stop, values in (("near", near), ("far", far)):
            for place, minutes in zip(("A", "B"), values, strict=True):
                rows.append((stop, place, minutes))
        return pd.DataFrame(rows, columns=["stop", "place", "minutes"])

    def test_it_is_the_walk_to_a_station_plus_its_journey_averaged_over_the_places(self):
        network, stations = self.setup()
        times = self.times(near=(30, 40), far=(10, 10))
        walk_near, walk_far = 400 / SPEED, 1600 / SPEED  # 5 and 20 minutes
        minutes = transport.travel_minutes(network, stations, times, [self.cell], walk=25)
        want_a = min(walk_near + 30, walk_far + 10)  # 30 by the far station
        want_b = min(walk_near + 40, walk_far + 10)
        assert minutes[self.cell] == pytest.approx((want_a + want_b) / 2, abs=0.3)

    def test_a_station_beyond_the_walk_is_not_a_choice(self):
        network, stations = self.setup()
        times = self.times(near=(30, 40), far=(1, 1))
        minutes = transport.travel_minutes(network, stations, times, [self.cell], walk=10)
        assert minutes[self.cell] == pytest.approx(400 / SPEED + 35, abs=0.3)

    def test_a_place_that_no_station_in_reach_gets_to_leaves_the_cell_without_a_value(self):
        network, stations = self.setup()
        times = self.times(near=(30, np.nan), far=(10, np.nan))
        minutes = transport.travel_minutes(network, stations, times, [self.cell], walk=25)
        assert np.isnan(minutes[self.cell])

    def test_with_no_station_in_reach_there_is_no_value(self):
        network, stations = self.setup()
        times = self.times(near=(30, 40), far=(10, 10))
        minutes = transport.travel_minutes(network, stations, times, [self.cell], walk=1)
        assert np.isnan(minutes[self.cell])
