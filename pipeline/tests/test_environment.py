import zipfile
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pytest
from shapely.geometry import Point, box

from atlas.datasets.countries.gb import os_open_greenspace
from atlas.indicators import environment
from atlas.spatial.grid import cell_centres_bng
from atlas.spatial.walking import SPEED, Network

HECTARE = 10_000.0


def square(x: float, y: float, hectares: float):
    side = (hectares * HECTARE) ** 0.5
    return box(x, y, x + side, y + side)


def greenspace_zip(tmp_path: Path, sites: list[tuple], points: list[tuple]) -> Path:
    """A file in the layout of OS Open Greenspace: sites are (id, function, geometry) and access
    points (site id, access type, x, y)."""
    package = tmp_path / "opgrsp_gb.gpkg"
    gpd.GeoDataFrame(
        {"id": [s[0] for s in sites], "function": [s[1] for s in sites]},
        geometry=[s[2] for s in sites],
        crs="EPSG:27700",
    ).to_file(package, layer="greenspace_site", driver="GPKG")
    gpd.GeoDataFrame(
        {
            "id": [f"p{i}" for i in range(len(points))],
            "access_type": [p[1] for p in points],
            "ref_to_greenspace_site": [p[0] for p in points],
        },
        geometry=[Point(p[2], p[3]) for p in points],
        crs="EPSG:27700",
    ).to_file(package, layer="access_point", driver="GPKG", mode="a")
    return package


EVERYWHERE = (0.0, 0.0, 700_000.0, 1_300_000.0)


class TestReadAccessPoints:
    def test_keeps_the_ways_in_on_foot_to_parks_and_playing_fields_of_two_hectares_or_more(
        self, tmp_path
    ):
        path = greenspace_zip(
            tmp_path,
            [
                ("park", "Public Park Or Garden", square(530000, 180000, 2.01)),
                ("field", "Playing Field", square(531000, 180000, 5.0)),
            ],
            [
                ("park", "Pedestrian", 530010, 180000),
                ("park", "Motor Vehicle And Pedestrian", 530020, 180000),
                ("field", "Pedestrian", 531010, 180000),
            ],
        )
        points = os_open_greenspace.read_access_points(path, EVERYWHERE)
        assert sorted(points[:, 0].tolist()) == [530010, 530020, 531010]

    @pytest.mark.parametrize(
        "function, hectares, access",
        [
            ("Public Park Or Garden", 1.9, "Pedestrian"),  # under 2 ha
            ("Play Space", 5.0, "Pedestrian"),
            ("Golf Course", 50.0, "Pedestrian"),
            ("Allotments Or Community Growing Spaces", 5.0, "Pedestrian"),
            ("Public Park Or Garden", 5.0, "Motor Vehicle"),  # a way in for cars only
        ],
    )
    def test_leaves_out_what_is_not_a_park_to_walk_to(self, tmp_path, function, hectares, access):
        path = greenspace_zip(
            tmp_path,
            [("site", function, square(530000, 180000, hectares))],
            [("site", access, 530010, 180000)],
        )
        assert len(os_open_greenspace.read_access_points(path, EVERYWHERE)) == 0

    def test_leaves_out_what_is_outside_the_bounds(self, tmp_path):
        path = greenspace_zip(
            tmp_path,
            [("a", "Public Park Or Garden", square(530000, 180000, 5.0))],
            [("a", "Pedestrian", 530010, 180000)],
        )
        assert len(os_open_greenspace.read_access_points(path, (0, 0, 1000, 1000))) == 0

    def test_downloads_the_great_britain_file_and_unpacks_its_geopackage(
        self, tmp_path, monkeypatch
    ):
        asked = []

        def fake_download(url, target):
            asked.append(url)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "w") as archive:
                archive.writestr("Data/opgrsp_gb.gpkg", "the package")
                archive.writestr("Doc/licence.txt", "a licence")

        monkeypatch.setattr(os_open_greenspace, "download", fake_download)
        path = os_open_greenspace.fetch(tmp_path)
        assert path.name == "opgrsp_gb.gpkg" and path.read_text(encoding="utf-8") == "the package"
        assert "OpenGreenspace" in asked[0] and "GeoPackage" in asked[0]


def test_the_minutes_to_the_nearest_way_into_a_park_follow_the_street():
    soho = h3.latlng_to_cell(51.5136, -0.1337, 9)
    x, y = cell_centres_bng([soho])[0]
    street = [(i, x - 400 + 80.0 * i, y) for i in range(11)]  # 80 m a node
    entrances = np.array([[x + 320, y], [x + 400, y]])
    minutes = environment.green_space_minutes(Network.from_ways([street]), entrances, [soho])
    assert minutes[soho] == pytest.approx(320 / SPEED, abs=0.2)
