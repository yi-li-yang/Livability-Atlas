import json

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.cities.london import tfl_bikepoints
from atlas.datasets.world import openstreetmap
from atlas.indicators import cycling
from atlas.spatial.grid import cell_centres_bng

TRACKS_OSM = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="51.5000" lon="-0.1000"/>
  <node id="2" lat="51.5000" lon="-0.0990"/>
  <node id="3" lat="51.5010" lon="-0.0990"/>
  <node id="4" lat="51.5100" lon="-0.1000"/>
  <node id="5" lat="51.5100" lon="-0.0990"/>
  <way id="10">
    <nd ref="1"/><nd ref="2"/><nd ref="3"/><tag k="highway" v="cycleway"/>
  </way>
  <way id="11">
    <nd ref="4"/><nd ref="5"/>
    <tag k="highway" v="primary"/><tag k="cycleway:left" v="track"/>
  </way>
  <way id="12">
    <nd ref="1"/><nd ref="4"/><tag k="highway" v="secondary"/><tag k="cycleway" v="lane"/>
  </way>
  <way id="13">
    <nd ref="2"/><nd ref="5"/><tag k="highway" v="footway"/><tag k="bicycle" v="yes"/>
  </way>
</osm>
"""


def test_osm_cycle_tracks_are_cycleways_and_tracks_beside_roads_not_painted_lanes(tmp_path):
    path = tmp_path / "tracks.osm"
    path.write_text(TRACKS_OSM, encoding="utf-8")
    segments = openstreetmap.read_cycle_tracks(path)
    # Way 10 has two segments and way 11 one; the painted lane and the footway are not tracks.
    assert len(segments) == 3
    assert list(segments.columns) == ["lng0", "lat0", "lng1", "lat1"]


CELL = h3.latlng_to_cell(51.5, -0.1, 9)


def test_the_track_within_a_radius_is_the_length_of_the_segments_whose_middle_is_in_it():
    x, y = cell_centres_bng([CELL])[0]
    segments = np.array(
        [
            [x, y, x + 300, y],  # 300 m, its middle 150 m away
            [x + 900, y, x + 1100, y],  # 200 m, its middle 1,000 m away: just in
            [x + 2000, y, x + 2500, y],  # out
        ]
    )
    km = cycling.track_km(segments, [CELL], radius=1000.0)
    assert km[0] == pytest.approx(0.5)


def test_no_track_gives_0_km():
    assert cycling.track_km(np.zeros((0, 4)), [CELL], radius=1000.0).tolist() == [0.0]


def test_the_docks_are_read_with_their_places(tmp_path):
    path = tmp_path / "bikepoints.json"
    path.write_text(
        json.dumps([{"id": "BikePoints_1", "name": "River Street", "lat": 51.53, "lon": -0.11}]),
        encoding="utf-8",
    )
    docks = tfl_bikepoints.read_docks(path)
    assert docks["id"].tolist() == ["BikePoints_1"]
    assert {"Easting", "Northing"} <= set(docks.columns)
    assert isinstance(docks, pd.DataFrame)
