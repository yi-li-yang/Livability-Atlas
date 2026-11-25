import io
import zipfile

import pytest

from atlas.datasets.cities.london import tfl_stationdata

HEADER = (
    "stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,location_type,parent_station,"
    "level_id,platform_code\n"
)
STOPS = (
    HEADER
    + """A,A,Alpha,,,,1,,,
A-Outside,,Outside Alpha,,,,3,A,,
A-Plat1,,Platform 1,,,,0,A,,1
A-Plat2,,Platform 2,,,,0,A,,2
B,B,Beta,,,,1,,,
B-Outside,,Outside Beta,,,,3,B,,
B-Plat1,,Platform 1,,,,0,B,,1
B-Plat2,,Platform 2,,,,0,B,,2
C,C,Gamma,,,,1,,,
C-Outside,,Outside Gamma,,,,3,C,,
C-Plat1,,Platform 1,,,,0,C,,1
"""
)

# Alpha: the street reaches a hall, and a lift from the hall reaches both platforms.
# Beta: a one-way ramp leads from platform 2 to the street only, so only platform 1 is reached.
# Gamma: no step-free path at all.
PATHWAYS = """pathway_id,from_stop_id,to_stop_id,pathway_mode,is_bidirectional
p1,A-Outside,A-Hall,1,1
p2,A-Hall,A-Plat1,5,1
p3,A-Plat2,A-Hall,5,1
p4,B-Outside,B-Plat1,1,1
p5,B-Plat2,B-Outside,1,0
"""

POINTS = """UniqueId,StationUniqueId,AreaName,AreaId,Level,Lat,Lon,FriendlyName
A-1,A,Entrance,1,0,51.50,-0.10,Entrance
A-2,A,Hall,2,0,51.52,-0.12,Hall
B-1,B,Entrance,1,0,51.60,-0.20,Entrance
C-1,C,Entrance,1,0,51.70,-0.30,Entrance
"""


def zipped(tmp_path, name: str, files: dict[str, str]):
    path = tmp_path / name
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for file, text in files.items():
            archive.writestr(file, text)
    path.write_bytes(buffer.getvalue())
    return path


@pytest.fixture
def stations(tmp_path):
    gtfs = zipped(tmp_path, "gtfs.zip", {"stops.txt": STOPS, "pathways.txt": PATHWAYS})
    detailed = zipped(tmp_path, "detailed.zip", {"StationPoints.csv": POINTS})
    return tfl_stationdata.read_stations(gtfs, detailed)


def test_it_counts_the_platforms_reached_step_free_from_the_street(stations):
    assert stations.loc["A", ["platforms", "step_free"]].tolist() == [2, 2]
    assert stations.loc["B", ["platforms", "step_free"]].tolist() == [2, 1]
    assert stations.loc["C", ["platforms", "step_free"]].tolist() == [1, 0]


def test_a_station_is_step_free_only_when_every_platform_is(stations):
    assert stations["all_step_free"].to_dict() == {"A": True, "B": False, "C": False}


def test_a_station_lies_at_the_mean_of_its_points(stations):
    assert stations.loc["A", "Latitude"] == pytest.approx(51.51)
    assert stations.loc["A", "Longitude"] == pytest.approx(-0.11)
    assert stations.loc["A", "name"] == "Alpha"


def test_the_family_walks_to_stations_step_free_at_every_platform(stations):
    from atlas.families.step_free import step_free_places

    places = step_free_places(stations)
    assert places.index.tolist() == ["A"]
    assert {"Easting", "Northing"} <= set(places.columns)
    assert 520_000 < places.loc["A", "Easting"] < 540_000


STATIONS_OSM = """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6">
  <node id="1" lat="51.4670" lon="-0.2420">
    <tag k="railway" v="station"/><tag k="name" v="Barnes"/><tag k="wheelchair" v="yes"/>
  </node>
  <node id="2" lat="51.4500" lon="-0.2000">
    <tag k="railway" v="station"/><tag k="name" v="Steps"/><tag k="wheelchair" v="limited"/>
  </node>
  <node id="3" lat="51.4400" lon="-0.1900">
    <tag k="railway" v="station"/><tag k="name" v="Untagged"/>
  </node>
  <node id="4" lat="51.4300" lon="-0.1800"><tag k="railway" v="halt"/></node>
</osm>
"""


def test_osm_stations_are_read_with_their_wheelchair_tag(tmp_path):
    from atlas.datasets.world import openstreetmap

    path = tmp_path / "stations.osm"
    path.write_text(STATIONS_OSM, encoding="utf-8")
    found = openstreetmap.read_stations(path)
    assert found["name"].tolist() == ["Barnes", "Steps", "Untagged"]
    assert found["wheelchair"].tolist()[:2] == ["yes", "limited"]
    assert found["wheelchair"].isna().tolist() == [False, False, True]


def test_an_osm_station_counts_only_away_from_tfl_s_stations_and_when_tagged_yes():
    import pandas as pd

    from atlas.families.step_free import beyond_tfl

    tfl = pd.DataFrame({"Latitude": [51.5000], "Longitude": [-0.1000]})
    osm = pd.DataFrame(
        {
            "name": ["Same as TfL's", "Barnes", "Steps"],
            "lat": [51.5005, 51.4670, 51.4500],
            "lng": [-0.1000, -0.2420, -0.2000],
            "wheelchair": ["yes", "yes", "limited"],
        }
    )
    found = beyond_tfl(osm, tfl)
    assert found["name"].tolist() == ["Barnes"]
    assert {"Easting", "Northing"} <= set(found.columns)
