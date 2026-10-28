import h3
import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.datasets.countries.gb import naptan
from atlas.indicators import transport
from atlas.spatial.walking import SPEED, Network

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
FROM_BNG = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)
SOHO = h3.latlng_to_cell(51.5136, -0.1337, 9)


def street_through(cell: str, length: float = 800.0) -> Network:
    """A straight street running east from 400 m west of the cell's centre, a node every 40 m."""
    lat, lng = h3.cell_to_latlng(cell)
    x, y = TO_BNG.transform(lng, lat)
    way = [(i, x - 400 + 40.0 * i, y) for i in range(int(length / 40) + 1)]
    return Network.from_ways([way])


def test_naptan_stations_are_the_active_rail_and_metro_entrances(tmp_path):
    path = tmp_path / "naptan.csv"
    path.write_text(
        "StopType,Status,Longitude,Latitude\n"
        "RLY,active,-0.12,51.50\n"  # a rail entrance
        "MET,active,-0.13,51.51\n"  # a metro entrance
        "BCT,active,-0.14,51.52\n"  # a bus stop
        "RLY,inactive,-0.15,51.53\n"  # a closed station
        "MET,active,,\n",  # no location
        encoding="utf-8",
    )
    stations = naptan.read_stations(path)
    assert stations["Longitude"].tolist() == [-0.12, -0.13]
    assert stations["Latitude"].tolist() == [51.50, 51.51]


def test_the_centres_of_cells_are_in_metres_of_british_national_grid():
    centres = transport.cell_centres([SOHO])
    assert 528_000 < centres[0, 0] < 531_000
    assert 180_000 < centres[0, 1] < 182_000


def test_the_minutes_to_a_station_follow_the_street():
    network = street_through(SOHO)
    x, y = transport.cell_centres([SOHO])[0]
    lng, lat = FROM_BNG.transform(x + 240, y)  # an entrance 240 m east, on the street
    stations = pd.DataFrame({"Longitude": [lng], "Latitude": [lat]})
    minutes = transport.station_minutes(network, stations, [SOHO])
    assert minutes[SOHO] == pytest.approx(240 / SPEED, abs=0.15)


def test_a_cell_far_from_the_street_walks_to_it_in_a_straight_line_first():
    network = street_through(SOHO)
    far = h3.latlng_to_cell(51.60, -0.30, 9)  # kilometres from the street
    x, y = transport.cell_centres([SOHO])[0]
    lng, lat = FROM_BNG.transform(x + 240, y)
    stations = pd.DataFrame({"Longitude": [lng], "Latitude": [lat]})
    minutes = transport.station_minutes(network, stations, [SOHO, far])
    assert np.isfinite(minutes[far])
    assert minutes[far] > 100  # a long straight leg to the street, then along it
