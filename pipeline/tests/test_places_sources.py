from pathlib import Path

import duckdb
import pandas as pd

from atlas.datasets.world import openstreetmap, overture


def overture_release(tmp_path: Path) -> str:
    """A small file in the layout of Overture's places, and the pattern that finds it."""
    folder = tmp_path / "theme=places" / "type=place"
    folder.mkdir(parents=True)
    rows = [
        # id, lng, lat, name, category, status
        ("a", -0.1337, 51.5136, "Soho Cafe", "cafe", "open"),
        ("b", -0.1400, 51.5200, "Old Pharmacy", "pharmacy", "permanently_closed"),
        ("c", 0.9000, 52.0000, "Far Away", "cafe", "open"),
        ("d", -0.1300, 51.5100, None, "library", "open"),
    ]
    values = ", ".join(
        f"('{i}', {lng}, {lat}, {'NULL' if name is None else repr(name)}, '{cat}', '{status}')"
        for i, lng, lat, name, cat, status in rows
    )
    duckdb.sql(f"""
        COPY (
          SELECT id,
                 {{'xmin': lng::DOUBLE, 'xmax': lng::DOUBLE,
                   'ymin': lat::DOUBLE, 'ymax': lat::DOUBLE}} AS bbox,
                 {{'primary': name}} AS names,
                 {{'primary': cat, 'hierarchy': [cat]}} AS taxonomy,
                 operating_status
          FROM (VALUES {values}) AS t(id, lng, lat, name, cat, operating_status)
        ) TO '{(folder / "part-0.parquet").as_posix()}' (FORMAT parquet)
    """)
    return (tmp_path / "theme=places" / "type=place" / "*").as_posix()


class TestOverture:
    def test_keeps_the_places_in_the_box_that_are_not_permanently_closed(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(overture, "source", lambda release: overture_release(tmp_path))
        path = overture.fetch(tmp_path / "data", "london", (-0.51, 51.28, 0.34, 51.69))
        assert path.name == f"places-london-{overture.RELEASE}.parquet"
        places = overture.read_places(path)
        assert sorted(places["id"]) == ["a", "d"]  # b is closed, c is outside the box
        cafe = places.set_index("id").loc["a"]
        assert (cafe["lng"], cafe["lat"], cafe["name"], cafe["category"]) == (
            -0.1337,
            51.5136,
            "Soho Cafe",
            "cafe",
        )

    def test_a_place_without_a_name_has_a_missing_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr(overture, "source", lambda release: overture_release(tmp_path))
        path = overture.fetch(tmp_path / "data", "london", (-0.51, 51.28, 0.34, 51.69))
        assert pd.isna(overture.read_places(path).set_index("id").loc["d", "name"])

    def test_a_file_already_kept_is_not_fetched_again(self, tmp_path, monkeypatch):
        folder = tmp_path / "data" / "raw" / "overture"
        folder.mkdir(parents=True)
        kept = folder / f"places-london-{overture.RELEASE}.parquet"
        kept.write_bytes(b"kept")

        def refuse(release):
            raise AssertionError("fetched again")

        monkeypatch.setattr(overture, "source", refuse)
        assert overture.fetch(tmp_path / "data", "london", (0, 0, 1, 1)) == kept


OSM = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6">
  <node id="1" lat="51.5136" lon="-0.1337">
    <tag k="amenity" v="cafe"/><tag k="name" v="Soho Cafe"/>
  </node>
  <node id="2" lat="51.5200" lon="-0.1400">
    <tag k="shop" v="supermarket"/><tag k="brand" v="Tesco"/>
  </node>
  <node id="3" lat="51.5300" lon="-0.1500"><tag k="amenity" v="bench"/></node>
  <node id="4" lat="51.5000" lon="-0.1000"/>
  <node id="5" lat="51.5000" lon="-0.1010"/>
  <node id="6" lat="51.5010" lon="-0.1010"/>
  <node id="7" lat="51.5010" lon="-0.1000"/>
  <node id="8" lat="51.5400" lon="-0.1600">
    <tag k="amenity" v="restaurant"/><tag k="cuisine" v="thai;noodle"/>
  </node>
  <node id="9" lat="51.5100" lon="-0.1200">
    <tag k="amenity" v="place_of_worship"/><tag k="religion" v="hindu"/><tag k="name" v="Mandir"/>
  </node>
  <way id="10">
    <nd ref="4"/><nd ref="5"/><nd ref="6"/><nd ref="7"/><nd ref="4"/>
    <tag k="leisure" v="fitness_centre"/><tag k="name" v="The Gym"/>
  </way>
</osm>
"""


class TestOpenStreetMapPlaces:
    def test_reads_tagged_places_from_points_and_the_middle_of_buildings(self, tmp_path):
        path = tmp_path / "small.osm"
        path.write_text(OSM, encoding="utf-8")
        places = openstreetmap.read_places(path)
        assert len(places) == 5  # the bench is not a place of a kind we count
        by_name = places.set_index(places["name"].fillna(places["brand"]))
        assert by_name.loc["Soho Cafe", "amenity"] == "cafe"
        assert by_name.loc["Tesco", "shop"] == "supermarket"
        gym = by_name.loc["The Gym"]
        assert gym["leisure"] == "fitness_centre"
        assert abs(gym["lat"] - 51.5005) < 1e-4 and abs(gym["lng"] - (-0.1005)) < 1e-4
        thai = places[places["amenity"] == "restaurant"].iloc[0]
        assert thai["cuisine"] == "thai;noodle"
        assert isinstance(places, pd.DataFrame)
        mandir = by_name.loc["Mandir"]
        assert mandir["amenity"] == "place_of_worship" and mandir["religion"] == "hindu"


class TestKeptPlaces:
    def test_places_are_read_once_per_extract(self, tmp_path, monkeypatch):
        extract = tmp_path / "raw" / "osm" / "greater-london.osm.pbf"
        extract.parent.mkdir(parents=True)
        extract.write_bytes(b"pbf")
        checksum_file = extract.with_name(extract.name + ".sha256")
        checksum_file.write_text("abcdef0123456789\n", encoding="utf-8")
        reads = []

        def fake_read(path):
            reads.append(path)
            return pd.DataFrame({"lng": [-0.1], "lat": [51.5], "name": ["A"]})

        monkeypatch.setattr(openstreetmap, "fetch", lambda data_dir, region_id: extract)
        monkeypatch.setattr(openstreetmap, "read_places", fake_read)
        first = openstreetmap.places(tmp_path, "london")
        second = openstreetmap.places(tmp_path, "london")
        assert len(reads) == 1 and first.equals(second)
        assert (extract.parent / "places-v2-london-abcdef012345.parquet").exists()
