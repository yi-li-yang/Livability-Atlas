"""The station-to-station matrix: a shortest-path search over the rides of the timetables."""

import numpy as np
import pandas as pd
import pytest

from atlas.indicators.station_matrix import UNREACHABLE, Ride, station_matrix

# Four stations on a line from west to east, 1 km apart, and a fifth 200 m north of C.
STATIONS = pd.DataFrame(
    {
        "stop": ["A", "B", "C", "D", "E"],
        "Easting": [0.0, 1000.0, 2000.0, 3000.0, 2000.0],
        "Northing": [0.0, 0.0, 0.0, 0.0, 200.0],
    }
)


def matrix(rides, headways, **kwargs):
    m = station_matrix(STATIONS, rides, headways, **kwargs)
    stops = list(STATIONS["stop"])
    return pd.DataFrame(m, index=stops, columns=stops)


def test_a_ride_costs_its_minutes_and_half_the_headway_to_board():
    rides = [Ride("red", "A", "B", 2), Ride("red", "B", "C", 3)]
    m = matrix(rides, {"red": 4})
    assert m.loc["A", "B"] == 2 + 2
    assert m.loc["A", "C"] == 2 + 2 + 3  # staying on the train costs no new wait
    assert m.loc["A", "A"] == 0


def test_rides_go_one_way_only_as_the_timetable_gives_them():
    m = matrix([Ride("red", "A", "B", 2)], {"red": 4})
    assert m.loc["B", "A"] == UNREACHABLE


def test_a_change_of_line_waits_for_the_new_line():
    rides = [Ride("red", "A", "B", 2), Ride("blue", "B", "D", 5)]
    m = matrix(rides, {"red": 4, "blue": 10})
    assert m.loc["A", "D"] == 2 + 2 + 5 + 5


def test_a_change_to_a_stop_nearby_walks_there():
    # E is 200 m from C: a walk of 200 x 1.33 / 80 = 3.325 minutes
    rides = [Ride("red", "A", "C", 6), Ride("green", "E", "D", 1)]
    m = matrix(rides, {"red": 2, "green": 2})
    assert m.loc["A", "D"] == round(1 + 6 + 3.325 + 1 + 1)


def test_stops_farther_apart_than_the_change_distance_are_not_joined():
    rides = [Ride("red", "A", "B", 2), Ride("green", "C", "D", 1)]
    m = matrix(rides, {"red": 2, "green": 2}, change_metres=300)
    assert m.loc["A", "D"] == UNREACHABLE


def test_the_quickest_of_two_ways_wins():
    rides = [
        Ride("slow", "A", "B", 10),
        Ride("slow", "B", "D", 10),
        Ride("fast", "A", "D", 6),
    ]
    m = matrix(rides, {"slow": 2, "fast": 30})
    assert m.loc["A", "D"] == min(1 + 20, 15 + 6)


def test_a_ride_between_unknown_stops_is_left_out():
    m = matrix([Ride("red", "A", "Z", 2)], {"red": 2})
    assert (np.asarray(m) >= 0).all()


def test_a_line_without_a_headway_is_an_error():
    with pytest.raises(KeyError):
        station_matrix(STATIONS, [Ride("red", "A", "B", 2)], {})


def test_a_ride_that_two_routes_share_is_not_counted_twice():
    rides = [Ride("red", "A", "B", 2), Ride("red", "A", "B", 3)]
    assert matrix(rides, {"red": 2}).loc["A", "B"] == 1 + 2


def test_each_cell_keeps_its_quickest_stations_within_the_walk():
    import h3

    from atlas.indicators.station_matrix import cell_stations
    from atlas.spatial.grid import cell_centres_bng
    from atlas.spatial.walking import SPEED, Network

    soho = h3.latlng_to_cell(51.5136, -0.1337, 9)
    far = h3.latlng_to_cell(51.70, -0.50, 9)
    x, y = cell_centres_bng([soho])[0]
    network = Network.from_ways([[(i, x - 400 + 40.0 * i, y) for i in range(41)]])
    stations = pd.DataFrame(
        {"stop": ["a", "b", "c"], "Easting": [x + 240, x - 120, x + 400], "Northing": [y, y, y]}
    )
    links = cell_stations(network, stations, [soho, far], walk=40, keep=2)
    assert [(c, s) for c, s, _ in links] == [(0, 1), (0, 0)]  # b, then a; c is third
    assert links[0][2] == pytest.approx(120 / SPEED, abs=0.15)
    assert links[1][2] == round(links[1][2], 1)  # tenths of a minute


def test_the_walks_between_street_and_platform_are_paid_at_each_end_and_each_change():
    rides = [Ride("red", "A", "B", 2), Ride("blue", "B", "D", 5)]
    m = matrix(rides, {"red": 4, "blue": 10}, board_minutes=2, alight_minutes=1)
    assert m.loc["A", "B"] == 2 + 2 + 2 + 1
    assert m.loc["A", "D"] == (2 + 2) + 2 + 1 + (2 + 5) + 5 + 1
