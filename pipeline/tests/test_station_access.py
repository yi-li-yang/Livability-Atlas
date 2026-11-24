"""Each cell's minutes to each station, on foot or on foot and by bus (spike S9)."""

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.indicators.station_access import bus_to_station, cell_access
from atlas.indicators.station_matrix import Ride
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import Network

STREET = 1.33 / 80  # minutes a metre of straight line, for a walk between a stop and a station


def places(**where: tuple[float, float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "stop": list(where),
            "Easting": [x for x, _ in where.values()],
            "Northing": [y for _, y in where.values()],
        }
    )


def as_dict(found_minutes: tuple[np.ndarray, np.ndarray]) -> dict[int, float]:
    found, minutes = found_minutes
    return {int(q): float(m) for q, m in zip(found, minutes, strict=True)}


class TestBusToStation:
    def test_a_stop_reaches_a_station_by_bus(self):
        # Wait half of 10 minutes, board in 0.5, ride 5, get off, walk 80 m to the station.
        stops = places(P=(0.0, 0.0), Q=(5000.0, 0.0))
        stations = places(S=(5080.0, 0.0))
        got = bus_to_station(stops, [Ride("L", "P", "Q", 5.0)], {"L": 10.0}, stations)
        assert got.shape == (1, 2)
        assert got[0, 0] == pytest.approx(5 + 0.5 + 5 + 80 * STREET, abs=1e-4)
        assert got[0, 1] == pytest.approx(80 * STREET, abs=1e-4)

    def test_a_bus_runs_only_the_way_its_timetable_gives(self):
        stops = places(P=(0.0, 0.0), Q=(5000.0, 0.0))
        stations = places(S=(-80.0, 0.0))
        got = bus_to_station(stops, [Ride("L", "P", "Q", 5.0)], {"L": 10.0}, stations)
        assert got[0, 0] == pytest.approx(80 * STREET, abs=1e-4)
        assert np.isinf(got[0, 1])

    def test_a_change_of_line_at_a_stop_waits_again(self):
        stops = places(P=(0.0, 0.0), Q=(5000.0, 0.0), R=(10000.0, 0.0))
        stations = places(S=(10080.0, 0.0))
        rides = [Ride("L1", "P", "Q", 5.0), Ride("L2", "Q", "R", 5.0)]
        got = bus_to_station(stops, rides, {"L1": 10.0, "L2": 20.0}, stations)
        want = (5 + 0.5 + 5) + (10 + 0.5 + 5) + 80 * STREET
        assert got[0, 0] == pytest.approx(want, abs=1e-4)

    def test_a_stop_farther_than_six_minutes_from_any_station_reaches_none_on_foot(self):
        # 400 m in a straight line is a walk of 6.65 minutes along the streets.
        stops = places(P=(0.0, 0.0), Q=(350.0, 0.0))
        stations = places(S=(400.0, 0.0))
        got = bus_to_station(stops, [], {}, stations)
        assert np.isinf(got[0, 0])
        assert got[0, 1] == pytest.approx(50 * STREET, abs=1e-4)

    def test_a_way_longer_than_the_reach_is_dropped(self):
        stops = places(P=(0.0, 0.0), Q=(5000.0, 0.0))
        stations = places(S=(5080.0, 0.0))
        got = bus_to_station(stops, [Ride("L", "P", "Q", 50.0)], {"L": 10.0}, stations)
        assert np.isinf(got[0, 0])

    def test_a_ride_through_a_stop_with_no_position_still_counts(self):
        stops = places(P=(0.0, 0.0), Q=(5000.0, 0.0))
        stations = places(S=(5080.0, 0.0))
        rides = [Ride("L", "P", "X", 2.0), Ride("L", "X", "Q", 3.0)]
        got = bus_to_station(stops, rides, {"L": 10.0}, stations)
        assert got[0, 0] == pytest.approx(5 + 0.5 + 5 + 80 * STREET, abs=1e-4)


class TestCellAccess:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)
    far = h3.latlng_to_cell(51.70, -0.50, 9)

    def street(self) -> tuple[Network, float, float]:
        x, y = cell_centres_bng([self.cell])[0]
        nodes = [(i, x - 2000 + 40.0 * i, y) for i in range(141)]  # 2 km west to 3.6 km east
        return Network.from_ways([nodes]), x, y

    def buses(self, x: float, y: float, ride: float, stop_at: float = 80.0):
        """A stop `stop_at` metres east of the centre, and a bus that rides `ride` minutes to a
        stop 40 m short of a station 3 km east, every 4 minutes."""
        stops = places(P=(x + stop_at, y), Q=(x + 2960, y))
        stations = places(near=(x + 400, y), S=(x + 3000, y))
        legs = bus_to_station(stops, [Ride("L", "P", "Q", ride)], {"L": 4.0}, stations)
        return stations, (stops, legs)

    def test_without_buses_the_access_is_the_walk(self):
        network, x, y = self.street()
        stations = places(a=(x + 240, y), b=(x - 120, y), c=(x + 3600, y))
        got = cell_access(network, stations, [self.cell, self.far], walk=40)
        xy = stations[["Easting", "Northing"]].to_numpy()
        walked = network.times_within(xy, cell_centres_bng([self.cell, self.far]), 40)
        assert [as_dict(g) for g in got] == [as_dict(w) for w in walked]
        assert list(got[0][0]) == sorted(got[0][0])  # stations in their order

    def test_a_cell_takes_the_bus_where_it_is_quicker(self):
        network, x, y = self.street()
        stations, buses = self.buses(x, y, ride=3.0)
        got = as_dict(cell_access(network, stations, [self.cell], buses=buses)[0])
        # A 1-minute walk to the stop, 2 + 0.5 to board, 3 to ride and 40 m to the station,
        # where the walk would take 37.5 minutes.
        assert got[1] == pytest.approx(1 + 2.5 + 3 + 40 * STREET, abs=0.05)

    def test_a_cell_keeps_the_walk_where_it_is_quicker(self):
        network, x, y = self.street()
        stations, buses = self.buses(x, y, ride=3.0)
        got = as_dict(cell_access(network, stations, [self.cell], buses=buses)[0])
        assert got[0] == pytest.approx(400 / 80, abs=0.05)

    def test_a_stop_beyond_the_stop_walk_is_not_used(self):
        network, x, y = self.street()
        stations, buses = self.buses(x, y, ride=3.0, stop_at=1200.0)  # a 15-minute walk
        got = as_dict(cell_access(network, stations, [self.cell], buses=buses)[0])
        assert got[1] == pytest.approx(3000 / 80, abs=0.05)

    def test_a_station_beyond_the_walk_is_kept_only_when_a_bus_reaches_it_in_time(self):
        network, x, y = self.street()
        stations, buses = self.buses(x, y, ride=3.0)
        walk_only = as_dict(cell_access(network, stations, [self.cell], walk=30)[0])
        with_bus = as_dict(cell_access(network, stations, [self.cell], walk=30, buses=buses)[0])
        assert 1 not in walk_only and 1 in with_bus
        _, slow = self.buses(x, y, ride=40.0)
        assert 1 not in as_dict(cell_access(network, stations, [self.cell], walk=30, buses=slow)[0])
