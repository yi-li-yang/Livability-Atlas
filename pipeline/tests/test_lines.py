import h3
import pandas as pd
import pytest

from atlas.datasets.cities.london import tfl_lines
from atlas.indicators import transport
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network


def stop(stop_id: str, lat: float = 51.5, lon: float = -0.1) -> dict:
    return {"id": stop_id, "lat": lat, "lon": lon}


class FakeTfl:
    """Answers TfL's Unified API from canned data."""

    def __init__(self, modes: dict[str, list[dict]], stops: dict[str, list[dict]]):
        self.modes, self.stops, self.asked = modes, stops, []

    def __call__(self, path: str):
        self.asked.append(path)
        if path.startswith("Line/Mode/"):
            return self.modes[path.removeprefix("Line/Mode/")]
        return self.stops[path.removeprefix("Line/").removesuffix("/StopPoints")]


def line(line_id: str, service: str = "Regular") -> dict:
    return {"id": line_id, "serviceTypes": [{"name": service}]}


class TestFetch:
    def make(self):
        return FakeTfl(
            {
                tfl_lines.RAIL_MODES: [line("victoria"), line("southeastern")],
                "bus": [line("1"), line("n1", "Night")],
            },
            {
                "victoria": [stop("S1"), stop("S2", 51.6)],
                "southeastern": [stop("S2", 51.6)],
                "1": [stop("B1"), stop("B2")],
            },
        )

    def test_it_keeps_a_row_for_each_line_at_each_stop(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tfl_lines, "PAUSE", 0)
        monkeypatch.setattr(tfl_lines, "_get", self.make())
        stops = tfl_lines.read_stops(tfl_lines.fetch(tmp_path))
        pairs = set(zip(stops["kind"], stops["line"], stops["stop"], strict=True))
        assert pairs == {
            ("rail", "victoria", "S1"),
            ("rail", "victoria", "S2"),
            ("rail", "southeastern", "S2"),
            ("bus", "1", "B1"),
            ("bus", "1", "B2"),
        }  # the night route is out
        assert stops.loc[stops["stop"] == "S2", "Latitude"].iloc[0] == pytest.approx(51.6)

    def test_it_is_fetched_once(self, tmp_path, monkeypatch):
        fake = self.make()
        monkeypatch.setattr(tfl_lines, "PAUSE", 0)
        monkeypatch.setattr(tfl_lines, "_get", fake)
        tfl_lines.fetch(tmp_path)
        asked = len(fake.asked)
        tfl_lines.fetch(tmp_path)
        assert len(fake.asked) == asked


def street_from(cell: str) -> tuple[Network, float, float]:
    x, y = cell_centres_bng([cell])[0]
    nodes = [(i, x - 400 + 80.0 * i, y) for i in range(31)]
    return Network.from_ways([nodes]), x, y


class TestLinesWithinAWalk:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def pairs(self, x: float, y: float) -> pd.DataFrame:
        rows = [  # (stop, line, metres east of the cell's centre)
            ("S1", "A", 240),
            ("S2", "A", 480),
            ("S2", "B", 480),
            ("S3", "C", 1800),
        ]
        return pd.DataFrame(
            {
                "stop": [r[0] for r in rows],
                "line": [r[1] for r in rows],
                "Easting": [x + r[2] for r in rows],
                "Northing": [y] * len(rows),
            }
        )

    def test_it_counts_each_line_once_however_many_stops_it_has_in_reach(self):
        network, x, y = street_from(self.cell)
        count = transport.lines_within_a_walk(network, self.pairs(x, y), [self.cell], minutes=12)
        assert count[self.cell] == 2  # A (at two stops) and B; C is 1,800 m away

    def test_a_shorter_walk_reaches_fewer_lines(self):
        network, x, y = street_from(self.cell)
        count = transport.lines_within_a_walk(network, self.pairs(x, y), [self.cell], minutes=4)
        assert count[self.cell] == 1  # 4 minutes is 320 m: only S1

    def test_a_cell_with_no_stop_in_reach_has_none(self):
        network, x, y = street_from(self.cell)
        far = self.pairs(x, y).iloc[3:]
        count = transport.lines_within_a_walk(network, far, [self.cell], minutes=12)
        assert count[self.cell] == 0

    def test_it_returns_whole_numbers(self):
        network, x, y = street_from(self.cell)
        count = transport.lines_within_a_walk(network, self.pairs(x, y), [self.cell], minutes=12)
        assert count.to_numpy().dtype.kind == "i"


def test_a_stopped_fetch_carries_on_without_asking_again(tmp_path, monkeypatch):
    monkeypatch.setattr(tfl_lines, "PAUSE", 0)
    calls = {"n": 0}
    fake = TestFetch().make()

    def flaky(path: str):
        if path == "Line/1/StopPoints" and calls["n"] == 0:
            calls["n"] += 1
            raise RuntimeError("TfL kept refusing")
        return fake(path)

    monkeypatch.setattr(tfl_lines, "_get", flaky)
    with pytest.raises(RuntimeError):
        tfl_lines.fetch(tmp_path)
    fake.asked.clear()
    tfl_lines.fetch(tmp_path)
    assert "Line/victoria/StopPoints" not in fake.asked  # the first lines were kept
